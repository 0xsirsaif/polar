from typing import Sequence
from uuid import UUID

import structlog
from sqlalchemy import and_, distinct
from sqlalchemy.orm import InstrumentedAttribute, joinedload

from polar.kit.services import ResourceService
from polar.models import Repository
from polar.models.issue import Issue
from polar.models.organization import Organization
from polar.models.pull_request import PullRequest
from polar.organization.schemas import RepositoryBadgeSettingsUpdate
from polar.postgres import AsyncSession, sql
from polar.worker import enqueue_job

from .schemas import RepositoryCreate, RepositoryUpdate

log = structlog.get_logger()


class RepositoryService(
    ResourceService[Repository, RepositoryCreate, RepositoryUpdate]
):
    @property
    def upsert_constraints(self) -> list[InstrumentedAttribute[int]]:
        return [self.model.external_id]

    async def get(
        self,
        session: AsyncSession,
        id: UUID,
        allow_deleted: bool = False,
        load_organization: bool = False,
    ) -> Repository | None:
        query = sql.select(Repository).where(Repository.id == id)

        if not allow_deleted:
            query = query.where(Repository.deleted_at.is_(None))

        if load_organization:
            query = query.options(joinedload(Repository.organization))

        res = await session.execute(query)
        return res.scalars().unique().one_or_none()

    async def list_by(
        self,
        session: AsyncSession,
        *,
        org_ids: list[UUID],
        repository_name: str | None = None,
        load_organization: bool = False,
        order_by_open_source: bool = False,
    ) -> Sequence[Repository]:
        statement = sql.select(Repository).where(
            Repository.organization_id.in_(org_ids),
            Repository.deleted_at.is_(None),
        )

        if repository_name:
            statement = statement.where(Repository.name == repository_name)

        if load_organization:
            statement = statement.options(joinedload(Repository.organization))

        if order_by_open_source:
            statement = statement.order_by(
                Repository.is_private, Repository.created_at.desc()
            )

        res = await session.execute(statement)
        return res.scalars().unique().all()

    async def get_by_org_and_name(
        self,
        session: AsyncSession,
        organization_id: UUID,
        name: str,
        load_organization: bool = False,
    ) -> Repository | None:
        statement = sql.select(Repository).where(
            Repository.organization_id == organization_id,
            Repository.deleted_at.is_(None),
            Repository.name == name,
        )

        if load_organization:
            statement = statement.options(joinedload(Repository.organization))

        res = await session.execute(statement)
        return res.scalars().unique().one_or_none()

    async def list_by_ids_and_organization(
        self,
        session: AsyncSession,
        repository_ids: Sequence[UUID],
        organization_id: UUID,
    ) -> Sequence[Repository]:
        statement = sql.select(Repository).where(
            Repository.organization_id == organization_id,
            Repository.deleted_at.is_(None),
            Repository.id.in_(repository_ids),
        )

        res = await session.execute(statement)
        return res.scalars().unique().all()

    async def update_badge_settings(
        self,
        session: AsyncSession,
        organization: Organization,
        repository: Repository,
        settings: RepositoryBadgeSettingsUpdate,
    ) -> RepositoryBadgeSettingsUpdate:
        enabled_auto_badge = False
        disabled_auto_badge = False

        if settings.badge_auto_embed is not None:
            if settings.badge_auto_embed and not repository.pledge_badge_auto_embed:
                enabled_auto_badge = True
            elif not settings.badge_auto_embed and repository.pledge_badge_auto_embed:
                disabled_auto_badge = True
            repository.pledge_badge_auto_embed = settings.badge_auto_embed

        await repository.save(session)
        log.info(
            "repository.update_badge_settings",
            repository_id=repository.id,
            settings=settings.dict(),
        )

        # Skip badge jobs for private repositories
        if repository.is_private:
            return settings

        if enabled_auto_badge and settings.retroactive:
            await enqueue_job(
                "github.badge.embed_retroactively_on_repository",
                organization.id,
                repository.id,
            )
        elif disabled_auto_badge and settings.retroactive:
            await enqueue_job(
                "github.badge.remove_on_repository", organization.id, repository.id
            )

        return settings

    async def get_repositories_synced_count(
        self,
        session: AsyncSession,
        organization: Organization,
    ) -> dict[UUID, dict[str, int]]:
        stmt = (
            sql.select(
                Repository.id,
                Issue.has_pledge_badge_label.label("labelled"),
                Issue.pledge_badge_embedded_at.is_not(None).label("embedded"),
                sql.func.count(distinct(Issue.id)).label("issue_count"),
                sql.func.count(distinct(PullRequest.id)).label("pull_request_count"),
            )
            .join(
                Issue,
                and_(Issue.repository_id == Repository.id, Issue.state == "open"),
                isouter=True,
            )
            .join(
                PullRequest,
                and_(
                    PullRequest.repository_id == Repository.id,
                    PullRequest.state == "open",
                ),
                isouter=True,
            )
            .where(
                Repository.organization_id == organization.id,
                Repository.deleted_at.is_(None),
            )
            .group_by(Repository.id, "labelled", "embedded")
        )

        res = await session.execute(stmt)
        rows = res.unique().all()

        prs: dict[UUID, bool] = {}
        ret: dict[UUID, dict[str, int]] = {}
        for r in rows:
            mapped = r._mapping
            repo_id = mapped["id"]
            repo = ret.setdefault(
                repo_id,
                {
                    "synced_issues": 0,
                    "auto_embedded_issues": 0,
                    "label_embedded_issues": 0,
                    # We get duplicate PR counts due to SQL grouping.
                    # So we only need to set it once at initation here.
                    "pull_requests": mapped["pull_request_count"],
                },
            )
            is_labelled = mapped["labelled"]
            repo["synced_issues"] += mapped["issue_count"]
            if repo_id not in prs:
                repo["synced_issues"] += mapped["pull_request_count"]
                prs[repo_id] = True

            if not mapped["embedded"]:
                continue

            if is_labelled:
                repo["label_embedded_issues"] += mapped["issue_count"]
            else:
                repo["auto_embedded_issues"] += mapped["issue_count"]

        return ret


repository = RepositoryService(Repository)
