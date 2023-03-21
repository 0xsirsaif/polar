from uuid import UUID
import structlog

from polar.integrations.github import service
from polar.models import Organization, Repository, Issue, PullRequest
from polar.postgres import AsyncSession
from polar.integrations.github import client as github
from polar.enums import Platforms
from polar.pull_request.schemas import FullPullRequestCreate
from polar.repository.schemas import RepositoryCreate

log = structlog.get_logger()

# ------------------------------------------------------------------------------
# TODO: Move all of this to service(s) except for true utils
# ------------------------------------------------------------------------------


async def get_organization_and_repo(
    session: AsyncSession,
    organization_id: UUID,
    repository_id: UUID,
) -> tuple[Organization, Repository]:
    organization = await service.github_organization.get(session, organization_id)
    if not organization:
        log.warning("no organization found", organization_id=organization_id)
        raise ValueError("no organization found")

    repository = await service.github_repository.get(session, repository_id)
    if not repository:
        log.warning("no repository found", repository_id=organization_id)
        raise ValueError("no repository found")

    return (organization, repository)


async def add_repositories(
    session: AsyncSession,
    organization: Organization,
    repositories: list[github.webhooks.InstallationCreatedPropRepositoriesItems],
) -> list[Repository]:
    schemas = []
    for repo in repositories:
        create_schema = RepositoryCreate(
            platform=Platforms.github,
            external_id=repo.id,
            organization_id=organization.id,
            name=repo.name,
            is_private=repo.private,
        )
        schemas.append(create_schema)

    log.debug("github.repositories.upsert_many", repos=schemas)
    instances = await service.github_repository.upsert_many(session, schemas)
    return instances


async def remove_repositories(
    session: AsyncSession,
    organization: Organization,
    repositories: list[
        github.webhooks.InstallationRepositoriesRemovedPropRepositoriesRemovedItems
    ],
) -> int:
    # TODO: Implement delete many to avoid N*2 db calls
    count = 0
    for repo in repositories:
        # TODO: All true now, but that will change
        res = await service.github_repository.delete(session, external_id=repo.id)
        if res:
            count += 1
    return count


async def upsert_issue(
    session: AsyncSession, event: github.webhooks.IssuesOpened
) -> Issue | None:
    repository_id = event.repository.id
    owner_id = event.repository.owner.id

    organization = await service.github_organization.get_by_external_id(
        session, owner_id
    )
    if not organization:
        # TODO: Raise here
        log.warning(
            "github.webhook.issue.opened",
            error="no organization found",
            organization_id=owner_id,
        )
        return None

    repository = await service.github_repository.get_by_external_id(
        session, repository_id
    )
    if not repository:
        # TODO: Raise here
        log.warning(
            "github.webhook.issue.opened",
            error="no repository found",
            repository_id=repository_id,
        )
        return None

    record = await service.github_issue.store(
        session, data=event.issue, organization=organization, repository=repository
    )
    return record


async def upsert_pull_request(
    session: AsyncSession, event: github.webhooks.PullRequestOpened
) -> PullRequest | None:
    repository_id = event.repository.id
    owner_id = event.repository.owner.id

    organization = await service.github_organization.get_by_external_id(
        session, owner_id
    )
    if not organization:
        # TODO: Raise here
        log.warning(
            "github.webhook.pull_request",
            error="no organization found",
            organization_id=owner_id,
        )
        return None

    repository = await service.github_repository.get_by_external_id(
        session, repository_id
    )
    if not repository:
        # TODO: Raise here
        log.warning(
            "github.webhook.pull_request",
            error="no repository found",
            repository_id=repository_id,
        )
        return None

    create_schema = FullPullRequestCreate.full_pull_request_from_github(
        event.pull_request,
        organization_id=organization.id,
        repository_id=repository.id,
    )
    record = await service.github_pull_request.upsert(session, create_schema)
    return record