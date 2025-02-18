from __future__ import annotations

from typing import List, Sequence, Tuple
from uuid import UUID

import structlog
from sqlalchemy import (
    ColumnElement,
    Integer,
    alias,
    and_,
    asc,
    desc,
    func,
    not_,
    nullslast,
    or_,
)
from sqlalchemy.orm import InstrumentedAttribute, aliased, contains_eager, joinedload

from polar.dashboard.schemas import IssueListType, IssueSortBy, IssueStatus
from polar.enums import Platforms
from polar.kit.services import ResourceService
from polar.kit.utils import utc_now
from polar.models.issue import Issue
from polar.models.issue_dependency import IssueDependency
from polar.models.issue_reference import IssueReference
from polar.models.organization import Organization
from polar.models.pledge import Pledge
from polar.models.repository import Repository
from polar.models.user import User
from polar.postgres import AsyncSession, sql

from .schemas import IssueCreate, IssueUpdate

log = structlog.get_logger()


class IssueService(ResourceService[Issue, IssueCreate, IssueUpdate]):
    @property
    def upsert_constraints(self) -> list[InstrumentedAttribute[int]]:
        return [self.model.external_id]

    async def get_loaded(
        self,
        session: AsyncSession,
        id: UUID,
    ) -> Issue | None:
        statement = (
            sql.select(Issue)
            .where(Issue.id == id)
            .where(Issue.deleted_at.is_(None))
            .options(
                joinedload(Issue.repository),
                joinedload(Issue.repository).joinedload(Repository.organization),
            )
        )
        res = await session.execute(statement)
        return res.scalars().unique().one_or_none()

    async def get_by_platform(
        self, session: AsyncSession, platform: Platforms, external_id: int
    ) -> Issue | None:
        return await self.get_by(session, platform=platform, external_id=external_id)

    async def get_by_number(
        self,
        session: AsyncSession,
        platform: Platforms,
        organization_id: UUID,
        repository_id: UUID,
        number: int,
    ) -> Issue | None:
        return await self.get_by(
            session,
            platform=platform,
            organization_id=organization_id,
            repository_id=repository_id,
            number=number,
        )

    async def list_by_repository(
        self, session: AsyncSession, repository_id: UUID
    ) -> Sequence[Issue]:
        statement = sql.select(Issue).where(Issue.repository_id == repository_id)
        res = await session.execute(statement)
        issues = res.scalars().unique().all()
        return issues

    async def list_by_repository_and_numbers(
        self, session: AsyncSession, repository_id: UUID, numbers: List[int]
    ) -> Sequence[Issue]:
        statement = (
            sql.select(Issue)
            .where(Issue.repository_id == repository_id)
            .where(Issue.number.in_(numbers))
        )
        res = await session.execute(statement)
        issues = res.scalars().unique().all()
        return issues

    async def list_by_repository_type_and_status(
        self,
        session: AsyncSession,
        repository_ids: list[UUID],
        issue_list_type: IssueListType,
        text: str | None = None,
        pledged_by_org: UUID
        | None = None,  # Only include issues that have been pledged by this org
        pledged_by_user: UUID
        | None = None,  # Only include issues that have been pledged by this user
        have_pledge: bool | None = None,  # If issues have pledge or not
        load_references: bool = False,
        load_pledges: bool = False,
        load_repository: bool = False,
        sort_by: IssueSortBy = IssueSortBy.newest,
        offset: int = 0,
        limit: int | None = None,
        include_statuses: list[IssueStatus] | None = None,
        have_polar_badge: bool | None = None,  # If issue has the polar badge or not
    ) -> Tuple[Sequence[Issue], int]:  # (issues, total_issue_count)
        pledge_by_organization = aliased(Organization)
        issue_repository = aliased(Repository)
        issue_organization = aliased(Organization, name="pledge_organization")

        statement = (
            sql.select(
                Issue,
                sql.func.count().over().label("total_count"),
            )
            .join(
                Issue.pledges,
                isouter=True,
            )
            .join(
                pledge_by_organization,
                Pledge.by_organization.of_type(pledge_by_organization),
                isouter=True,
            )
            .join(
                Pledge.user,
                isouter=True,
            )
        )

        if issue_list_type == IssueListType.issues:
            statement = statement.where(Issue.repository_id.in_(repository_ids))
        elif issue_list_type == IssueListType.dependencies:
            if not pledged_by_org and not pledged_by_user:
                raise ValueError("no pledge_by criteria specified")

            statement = statement.join(
                IssueDependency,
                IssueDependency.dependency_issue_id == Issue.id,
                isouter=True,
            )

            pledge_criterias: list[ColumnElement[bool]] = []
            if pledged_by_org:
                pledge_criterias.append(Pledge.by_organization_id == pledged_by_org)

            if pledged_by_user:
                pledge_criterias.append(Pledge.by_user_id == pledged_by_user)

            statement = statement.where(
                or_(
                    IssueDependency.repository_id.in_(repository_ids),
                    # Pledge.id.is_(None),
                    or_(*pledge_criterias),
                ),
            )

        else:
            raise ValueError(f"Unknown issue list type: {issue_list_type}")

        # pledge filter
        if have_pledge is not None:
            if have_pledge:
                statement = statement.where(Pledge.id.is_not(None))
            else:
                statement = statement.where(Pledge.id.is_(None))

        if have_polar_badge is not None:
            statement = statement.where(
                Issue.pledge_badge_currently_embedded == have_polar_badge
            )

        if include_statuses:
            conds: list[ColumnElement[bool]] = []

            is_closed = Issue.issue_closed_at.is_not(None)

            is_pull_request = Issue.issue_has_pull_request_relationship.is_(True)

            is_in_progress = Issue.issue_has_in_progress_relationship.is_(True)

            is_triaged = or_(Issue.assignee.is_not(None), Issue.assignees.is_not(None))

            # backlog
            is_backlog: ColumnElement[bool] = and_(
                not_(is_triaged),
                not_(is_in_progress),
                not_(is_pull_request),
                not_(is_closed),
            )

            for status in include_statuses:
                if status == IssueStatus.backlog:
                    conds.append(is_backlog)

                if status == IssueStatus.triaged:
                    conds.append(
                        and_(
                            is_triaged,
                            not_(is_in_progress),
                            not_(is_pull_request),
                            not_(is_closed),
                        )
                    )

                if status == IssueStatus.in_progress:
                    conds.append(
                        and_(
                            is_in_progress,
                            not_(is_pull_request),
                            not_(is_closed),
                        )
                    )

                if status == IssueStatus.pull_request:
                    conds.append(
                        and_(
                            is_pull_request,
                            not_(is_closed),
                        )
                    )

                if status == IssueStatus.closed:
                    conds.append(
                        and_(
                            is_closed,
                        )
                    )

            statement = statement.where(or_(*conds))

        # free text search
        if text:
            # Search in titles using the vector index
            # https://www.postgresql.org/docs/current/textsearch-controls.html#TEXTSEARCH-PARSING-QUERIES
            #
            # The index supports fast matching of words and prefix-matching of words
            #
            # Here we're converting a user query like "feat cli" to
            # "feat:* | cli:*"
            words = text.split(" ")

            # remove empty words
            words = [w for w in words if len(w.strip()) > 0]

            # convert all words to prefix matches
            words = [f"{w}:*" for w in words]

            # OR all words
            search = " | ".join(words)

            statement = statement.where(
                Issue.title_tsv.bool_op("@@")(func.to_tsquery(search))
            )

            # Sort results based on matching
            if sort_by == IssueSortBy.relevance:
                statement = statement.order_by(
                    desc(func.ts_rank_cd(Issue.title_tsv, func.to_tsquery(search)))
                )

        if sort_by == IssueSortBy.issues_default:
            statement = statement.order_by(
                desc(Issue.pledged_amount_sum),
                desc(Issue.total_engagement_count),
                desc(Issue.issue_modified_at),
            )
        elif sort_by == IssueSortBy.newest:
            statement = statement.order_by(
                desc(Issue.issue_created_at),
            )
        elif sort_by == IssueSortBy.relevance:
            pass  # handled above
        elif sort_by == IssueSortBy.pledged_amount_desc:
            statement = statement.order_by(
                desc(Issue.pledged_amount_sum),
                desc(Issue.issue_modified_at),
            )
        elif sort_by == IssueSortBy.dependencies_default:
            statement = statement.order_by(
                nullslast(desc(sql.func.sum(Pledge.amount))),
                desc(Issue.issue_modified_at),
            )
        elif sort_by == IssueSortBy.recently_updated:
            statement = statement.order_by(desc(Issue.issue_modified_at))
        elif sort_by == IssueSortBy.least_recently_updated:
            statement = statement.order_by(asc(Issue.issue_modified_at))
        elif sort_by == IssueSortBy.most_engagement:
            statement = statement.order_by(
                desc(Issue.total_engagement_count),
                desc(Issue.issue_modified_at),
            )
        elif sort_by == IssueSortBy.most_positive_reactions:
            statement = statement.order_by(
                desc(Issue.positive_reactions_count),
                desc(Issue.issue_modified_at),
            )
        elif sort_by == IssueSortBy.funding_goal_desc_and_most_positive_reactions:
            statement = statement.order_by(
                nullslast(desc(Issue.funding_goal)),
                desc(Issue.positive_reactions_count),
                desc(Issue.issue_modified_at),
            )
        else:
            raise Exception("unknown sort_by")

        if load_references:
            statement = statement.options(
                joinedload(Issue.references).joinedload(IssueReference.pull_request)
            )

        if load_pledges:
            statement = statement.options(
                contains_eager(Issue.pledges),
                contains_eager(Issue.pledges).contains_eager(Pledge.user),
                contains_eager(Issue.pledges).contains_eager(
                    Pledge.by_organization.of_type(pledge_by_organization)
                ),
            )
            statement = statement.group_by(
                Issue.id,
                Pledge.id,
                User.id,
                pledge_by_organization.id,
            )

        elif load_repository:
            statement = statement.join(
                issue_repository,
                Issue.repository.of_type(issue_repository),
                isouter=False,
            )

            statement = statement.join(
                issue_organization, issue_repository.organization, isouter=False
            )

            statement = statement.options(
                contains_eager(
                    Issue.repository.of_type(issue_repository)
                ).contains_eager(
                    issue_repository.organization.of_type(issue_organization)
                )
            )

            statement = statement.group_by(
                Issue.id,
                issue_repository.id,
                issue_organization.id,
            )

        else:
            statement = statement.group_by(
                Issue.id,
            )

        if limit:
            statement = statement.limit(limit).offset(offset)

        res = await session.execute(statement)
        rows = res.unique().all()

        total_count = rows[0][1] if len(rows) > 0 else 0
        issues = [r[0] for r in rows]

        return (issues, total_count)

    async def list_issue_references(
        self,
        session: AsyncSession,
        issue: Issue,
    ) -> Sequence[IssueReference]:
        stmt = (
            sql.select(IssueReference)
            .where(
                IssueReference.issue_id == issue.id,
            )
            .options(joinedload(IssueReference.pull_request))
        )
        res = await session.execute(stmt)
        refs = res.scalars().unique().all()
        return refs

    async def list_issue_references_for_issues(
        self, session: AsyncSession, issue_ids: list[UUID]
    ) -> Sequence[IssueReference]:
        stmt = (
            sql.select(IssueReference)
            .where(
                IssueReference.issue_id.in_(issue_ids),
            )
            .options(joinedload(IssueReference.pull_request))
        )
        res = await session.execute(stmt)
        refs = res.scalars().unique().all()
        return refs

    async def list_issue_dependencies_for_repositories(
        self,
        session: AsyncSession,
        repos: Sequence[Repository],
    ) -> Sequence[IssueDependency]:
        """
        Returns a dict of issue_id -> list of issues dependent on that issue
        """
        stmt = (
            sql.select(IssueDependency)
            .where(IssueDependency.repository_id.in_(list({r.id for r in repos})))
            .options(
                joinedload(IssueDependency.dependent_issue),
                joinedload(IssueDependency.dependency_issue),
            )
        )
        res = await session.execute(stmt)
        deps = res.scalars().unique().all()
        return deps

    async def update_issue_reference_state(
        self,
        session: AsyncSession,
        issue: Issue,
    ) -> None:
        refs = await self.list_issue_references(session, issue)

        in_progress = False
        pull_request = False

        for r in refs:
            if r.pull_request and not r.pull_request.is_draft:
                pull_request = True
            else:
                in_progress = True

        stmt = (
            sql.update(Issue)
            .where(Issue.id == issue.id)
            .values(
                issue_has_in_progress_relationship=in_progress,
                issue_has_pull_request_relationship=pull_request,
            )
        )

        await session.execute(stmt)
        await session.commit()

    async def mark_confirmed_solved(
        self,
        session: AsyncSession,
        issue_id: UUID,
        by_user_id: UUID,
    ) -> None:
        stmt = (
            sql.update(Issue)
            .where(Issue.id == issue_id, Issue.confirmed_solved_at.is_(None))
            .values(
                confirmed_solved_at=utc_now(),
                confirmed_solved_by=by_user_id,
            )
        )

        await session.execute(stmt)
        await session.commit()


issue = IssueService(Issue)
