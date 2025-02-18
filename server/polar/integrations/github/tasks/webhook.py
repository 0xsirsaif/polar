from typing import Any, Sequence, Union

import structlog

from polar.context import ExecutionContext
from polar.integrations.github import client as github
from polar.kit.extensions.sqlalchemy import sql
from polar.kit.utils import utc_now
from polar.models.issue import Issue
from polar.models.organization import Organization
from polar.organization.hooks import OrganizationHook, organization_upserted
from polar.postgres import AsyncSession, AsyncSessionLocal
from polar.worker import JobContext, PolarWorkerContext, enqueue_job, task

from .. import service
from .utils import (
    get_event_issue,
    get_organization_and_repo,
    remove_repositories,
    upsert_issue,
    upsert_pull_request,
)

log = structlog.get_logger()


# ------------------------------------------------------------------------------
# REPOSITORIES
# ------------------------------------------------------------------------------


async def repositories_changed(
    session: AsyncSession,
    event: Union[
        github.webhooks.InstallationRepositoriesAdded,
        github.webhooks.InstallationRepositoriesRemoved,
        github.webhooks.InstallationCreated,
    ],
) -> None:
    with ExecutionContext(is_during_installation=True):
        removed: Sequence[
            Union[
                github.webhooks.InstallationRepositoriesRemovedPropRepositoriesRemovedItems,
                github.webhooks.InstallationRepositoriesAddedPropRepositoriesRemovedItems,
                github.webhooks.InstallationRepositoriesRemovedPropRepositoriesRemovedItems,
            ]
        ] = (
            []
            if isinstance(event, github.webhooks.InstallationCreated)
            else event.repositories_removed
        )

        org = await create_from_installation(
            session,
            event.installation,
            removed,
        )

        # Sync permission for the installing user
        sender = await service.github_user.get_user_by_github_id(
            session, event.sender.id
        )
        if sender:
            await service.github_user.sync_github_admin_orgs(session, user=sender)

        # send after members have been added
        await organization_upserted.call(OrganizationHook(session, org))


async def create_from_installation(
    session: AsyncSession,
    installation: Union[
        github.rest.Installation,
        github.webhooks.Installation,
    ],
    removed: Sequence[
        Union[
            github.webhooks.InstallationRepositoriesRemovedPropRepositoriesRemovedItems,
            github.webhooks.InstallationRepositoriesAddedPropRepositoriesRemovedItems,
            github.webhooks.InstallationRepositoriesRemovedPropRepositoriesRemovedItems,
        ]
    ],
) -> Organization:
    organization = await service.github_organization.update_or_create_from_github(
        session,
        installation,
    )

    if removed:
        await remove_repositories(session, removed)

    await service.github_repository.install_for_organization(
        session, organization, installation.id
    )

    return organization


@task("github.webhook.installation_repositories.added")
async def repositories_added(
    ctx: JobContext,
    scope: str,
    action: str,
    payload: dict[str, Any],
    polar_context: PolarWorkerContext,
) -> None:
    with polar_context.to_execution_context():
        parsed = github.webhooks.parse_obj(scope, payload)
        if not isinstance(parsed, github.webhooks.InstallationRepositoriesAdded):
            log.error("github.webhook.unexpected_type")
            raise Exception("unexpected webhook payload")
        async with AsyncSessionLocal() as session:
            await repositories_changed(session, parsed)


@task(name="github.webhook.installation_repositories.removed")
async def repositories_removed(
    ctx: JobContext,
    scope: str,
    action: str,
    payload: dict[str, Any],
    polar_context: PolarWorkerContext,
) -> None:
    with polar_context.to_execution_context():
        parsed = github.webhooks.parse_obj(scope, payload)
        if not isinstance(parsed, github.webhooks.InstallationRepositoriesRemoved):
            log.error("github.webhook.unexpected_type")
            raise Exception("unexpected webhook payload")
        async with AsyncSessionLocal() as session:
            await repositories_changed(session, parsed)


@task(name="github.webhook.public")
async def repositories_public(
    ctx: JobContext,
    scope: str,
    action: str,
    payload: dict[str, Any],
    polar_context: PolarWorkerContext,
) -> None:
    with polar_context.to_execution_context():
        parsed = github.webhooks.parse_obj(scope, payload)
        if not isinstance(parsed, github.webhooks.PublicEvent):
            log.error("github.webhook.unexpected_type")
            raise Exception("unexpected webhook payload")
        async with AsyncSessionLocal() as session:
            await repository_updated(session, parsed)


@task(name="github.webhook.repository.renamed")
async def repositories_renamed(
    ctx: JobContext,
    scope: str,
    action: str,
    payload: dict[str, Any],
    polar_context: PolarWorkerContext,
) -> None:
    with polar_context.to_execution_context():
        parsed = github.webhooks.parse_obj(scope, payload)
        if not isinstance(parsed, github.webhooks.RepositoryRenamed):
            log.error("github.webhook.unexpected_type")
            raise Exception("unexpected webhook payload")
        async with AsyncSessionLocal() as session:
            await repository_updated(session, parsed)


@task(name="github.webhook.repository.edited")
async def repositories_redited(
    ctx: JobContext,
    scope: str,
    action: str,
    payload: dict[str, Any],
    polar_context: PolarWorkerContext,
) -> None:
    with polar_context.to_execution_context():
        parsed = github.webhooks.parse_obj(scope, payload)
        if not isinstance(parsed, github.webhooks.RepositoryEdited):
            log.error("github.webhook.unexpected_type")
            raise Exception("unexpected webhook payload")
        async with AsyncSessionLocal() as session:
            await repository_updated(session, parsed)


@task(name="github.webhook.repository.deleted")
async def repositories_deleted(
    ctx: JobContext,
    scope: str,
    action: str,
    payload: dict[str, Any],
    polar_context: PolarWorkerContext,
) -> None:
    with polar_context.to_execution_context():
        parsed = github.webhooks.parse_obj(scope, payload)
        if not isinstance(parsed, github.webhooks.RepositoryDeleted):
            log.error("github.webhook.unexpected_type")
            raise Exception("unexpected webhook payload")
        async with AsyncSessionLocal() as session:
            await repository_deleted(session, parsed)


@task(name="github.webhook.repository.archived")
async def repositories_archived(
    ctx: JobContext,
    scope: str,
    action: str,
    payload: dict[str, Any],
    polar_context: PolarWorkerContext,
) -> None:
    with polar_context.to_execution_context():
        parsed = github.webhooks.parse_obj(scope, payload)
        if not isinstance(parsed, github.webhooks.RepositoryArchived):
            log.error("github.webhook.unexpected_type")
            raise Exception("unexpected webhook payload")
        async with AsyncSessionLocal() as session:
            await repository_updated(session, parsed)


async def repository_updated(
    session: AsyncSession,
    event: Union[
        github.webhooks.PublicEvent,
        github.webhooks.RepositoryRenamed,
        github.webhooks.RepositoryEdited,
        github.webhooks.RepositoryArchived,
    ],
) -> dict[str, Any]:
    with ExecutionContext(is_during_installation=True):
        if not event.installation:
            return dict(success=False)

        repository = await service.github_repository.get_by_external_id(
            session, event.repository.id
        )
        if not repository:
            return dict(success=False)

        repository.is_private = event.repository.visibility == "private"
        repository.name = event.repository.name
        repository.is_archived = event.repository.archived

        await repository.save(session)

        return dict(success=True)


async def repository_deleted(
    session: AsyncSession,
    event: github.webhooks.RepositoryDeleted,
) -> dict[str, Any]:
    with ExecutionContext(is_during_installation=True):
        if not event.installation:
            return dict(success=False)

        repository = await service.github_repository.get_by_external_id(
            session, event.repository.id
        )
        if not repository:
            return dict(success=False)

        if not repository.deleted_at:
            repository.deleted_at = utc_now()

        await repository.save(session)

        return dict(success=True)


# ------------------------------------------------------------------------------
# ISSUES
# ------------------------------------------------------------------------------


async def handle_issue(
    session: AsyncSession,
    scope: str,
    action: str,
    event: Union[
        github.webhooks.IssuesOpened,
        github.webhooks.IssuesEdited,
        github.webhooks.IssuesClosed,
        github.webhooks.IssuesReopened,
        github.webhooks.IssuesDeleted,
    ],
) -> Issue:
    issue = await upsert_issue(session, event)
    if not issue:
        raise Exception(f"failed to save issue external_id={event.issue.id}")

    # Trigger references sync job for entire repository
    await enqueue_job(
        "github.repo.sync.issue_references", issue.organization_id, issue.repository_id
    )

    return issue


@task("github.webhook.issues.opened")
async def issue_opened(
    ctx: JobContext,
    scope: str,
    action: str,
    payload: dict[str, Any],
    polar_context: PolarWorkerContext,
) -> None:
    with polar_context.to_execution_context():
        parsed = github.webhooks.parse_obj(scope, payload)
        if not isinstance(parsed, github.webhooks.IssuesOpened):
            log.error("github.webhook.unexpected_type")
            raise Exception("unexpected webhook payload")

        async with AsyncSessionLocal() as session:
            issue = await handle_issue(session, scope, action, parsed)

            # Add badge if has label
            if issue.has_pledge_badge_label:
                await update_issue_embed(session, issue=issue, embed=True)


@task("github.webhook.issues.reopened")
async def issue_reopened(
    ctx: JobContext,
    scope: str,
    action: str,
    payload: dict[str, Any],
    polar_context: PolarWorkerContext,
) -> None:
    with polar_context.to_execution_context():
        parsed = github.webhooks.parse_obj(scope, payload)
        if not isinstance(parsed, github.webhooks.IssuesReopened):
            log.error("github.webhook.unexpected_type")
            raise Exception("unexpected webhook payload")

        async with AsyncSessionLocal() as session:
            issue = await handle_issue(session, scope, action, parsed)

            # Add badge if has label
            if issue.has_pledge_badge_label:
                await update_issue_embed(session, issue=issue, embed=True)


@task("github.webhook.issues.edited")
async def issue_edited(
    ctx: JobContext,
    scope: str,
    action: str,
    payload: dict[str, Any],
    polar_context: PolarWorkerContext,
) -> None:
    with polar_context.to_execution_context():
        parsed = github.webhooks.parse_obj(scope, payload)
        if not isinstance(parsed, github.webhooks.IssuesEdited):
            log.error("github.webhook.unexpected_type")
            raise Exception("unexpected webhook payload")

        async with AsyncSessionLocal() as session:
            issue = await handle_issue(session, scope, action, parsed)

            # Add badge if has label
            if issue.has_pledge_badge_label:
                await update_issue_embed(session, issue=issue, embed=True)


@task("github.webhook.issues.closed")
async def issue_closed(
    ctx: JobContext,
    scope: str,
    action: str,
    payload: dict[str, Any],
    polar_context: PolarWorkerContext,
) -> None:
    with polar_context.to_execution_context():
        parsed = github.webhooks.parse_obj(scope, payload)
        if not isinstance(parsed, github.webhooks.IssuesClosed):
            log.error("github.webhook.unexpected_type")
            raise Exception("unexpected webhook payload")

        async with AsyncSessionLocal() as session:
            await handle_issue(session, scope, action, parsed)


@task("github.webhook.issues.deleted")
async def issue_deleted(
    ctx: JobContext,
    scope: str,
    action: str,
    payload: dict[str, Any],
    polar_context: PolarWorkerContext,
) -> None:
    with polar_context.to_execution_context():
        parsed = github.webhooks.parse_obj(scope, payload)
        if not isinstance(parsed, github.webhooks.IssuesDeleted):
            log.error("github.webhook.unexpected_type")
            raise Exception("unexpected webhook payload")

        async with AsyncSessionLocal() as session:
            # Save last known version
            await handle_issue(session, scope, action, parsed)

            # Mark as deleted
            issue = await get_event_issue(session, parsed)
            if not issue:
                return None

            await service.github_issue.soft_delete(session, issue.id)


@task("github.webhook.issues.labeled")
async def issue_labeled(
    ctx: JobContext,
    scope: str,
    action: str,
    payload: dict[str, Any],
    polar_context: PolarWorkerContext,
) -> None:
    with polar_context.to_execution_context():
        parsed = github.webhooks.parse_obj(scope, payload)
        if not isinstance(parsed, github.webhooks.IssuesLabeled):
            log.error("github.webhook.unexpected_type")
            raise Exception("unexpected webhook payload")

        async with AsyncSessionLocal() as session:
            await issue_labeled_async(session, scope, action, parsed)


@task("github.webhook.issues.unlabeled")
async def issue_unlabeled(
    ctx: JobContext,
    scope: str,
    action: str,
    payload: dict[str, Any],
    polar_context: PolarWorkerContext,
) -> None:
    with polar_context.to_execution_context():
        parsed = github.webhooks.parse_obj(scope, payload)
        if not isinstance(parsed, github.webhooks.IssuesUnlabeled):
            log.error("github.webhook.unexpected_type")
            raise Exception("unexpected webhook payload")

        async with AsyncSessionLocal() as session:
            await issue_labeled_async(session, scope, action, parsed)


async def update_issue_embed(
    session: AsyncSession,
    *,
    issue: Issue,
    embed: bool = False,
) -> bool:
    try:
        org, repo = await get_organization_and_repo(
            session, issue.organization_id, issue.repository_id
        )
    except ValueError:
        log.error(
            "github.webhook.issues.badge",
            error="no org/repo",
            issue_id=issue.id,
        )
        return False

    if embed:
        res = await service.github_issue.embed_badge(
            session,
            organization=org,
            repository=repo,
            issue=issue,
            triggered_from_label=True,
        )
        log.info(
            "github.webhook.issues.badge.embed",
            success=res,
            issue_id=issue.id,
        )
        return res

    # Do not remove the badge if automatic badging is enabled
    if repo.pledge_badge_auto_embed:
        return False

    # TODO: Implement logging here too as with `embed`
    # However, we need to first update `remove_badge` to return a true bool
    return await service.github_issue.remove_badge(
        session,
        organization=org,
        repository=repo,
        issue=issue,
        triggered_from_label=True,
    )


async def issue_labeled_async(
    session: AsyncSession,
    scope: str,
    action: str,
    event: Union[
        github.webhooks.IssuesLabeled,
        github.webhooks.IssuesUnlabeled,
    ],
) -> None:
    issue = await service.github_issue.get_by_external_id(session, event.issue.id)
    if not issue:
        log.warn(
            "github.webhook.issue_labeled_async.not_found", external_id=event.issue.id
        )
        return

    had_polar_label = issue.has_pledge_badge_label
    issue = await service.github_issue.set_labels(session, issue, event.issue.labels)

    log.info(
        "github.webhook.issues.label",
        action=action,
        issue_id=issue.id,
        label=event.label.name,
        had_polar_label=had_polar_label,
        should_have_polar_label=issue.has_pledge_badge_label,
    )

    # Add/remove polar badge if label has changed
    if event.label.name == "polar":
        await update_issue_embed(
            session, issue=issue, embed=issue.has_pledge_badge_label
        )


@task("github.webhook.issues.assigned")
async def issue_assigned(
    ctx: JobContext,
    scope: str,
    action: str,
    payload: dict[str, Any],
    polar_context: PolarWorkerContext,
) -> None:
    with polar_context.to_execution_context():
        parsed = github.webhooks.parse_obj(scope, payload)
        if not isinstance(parsed, github.webhooks.IssuesAssigned):
            log.error("github.webhook.unexpected_type")
            raise Exception("unexpected webhook payload")

        async with AsyncSessionLocal() as session:
            await issue_assigned_async(session, scope, action, parsed)


@task("github.webhook.issues.unassigned")
async def issue_unassigned(
    ctx: JobContext,
    scope: str,
    action: str,
    payload: dict[str, Any],
    polar_context: PolarWorkerContext,
) -> None:
    with polar_context.to_execution_context():
        parsed = github.webhooks.parse_obj(scope, payload)
        if not isinstance(parsed, github.webhooks.IssuesUnassigned):
            log.error("github.webhook.unexpected_type")
            raise Exception("unexpected webhook payload")

        async with AsyncSessionLocal() as session:
            await issue_assigned_async(session, scope, action, parsed)


async def issue_assigned_async(
    session: AsyncSession,
    scope: str,
    action: str,
    event: Union[
        github.webhooks.IssuesAssigned,
        github.webhooks.IssuesUnassigned,
    ],
) -> None:
    issue = await service.github_issue.get_by_external_id(session, event.issue.id)
    if not issue:
        log.warn(
            "github.webhook.issue_assigned_async.not_found", external_id=event.issue.id
        )
        return

    # modify assignee
    stmt = (
        sql.Update(Issue)
        .where(Issue.id == issue.id)
        .values(
            assignee=github.jsonify(event.issue.assignee),
            assignees=github.jsonify(event.issue.assignees),
            issue_modified_at=event.issue.updated_at,
        )
    )
    await session.execute(stmt)
    await session.commit()


# ------------------------------------------------------------------------------
# PULL REQUESTS
# ------------------------------------------------------------------------------


async def handle_pull_request(
    session: AsyncSession,
    scope: str,
    action: str,
    event: Union[
        github.webhooks.PullRequestOpened,
        github.webhooks.PullRequestEdited,
        github.webhooks.PullRequestClosed,
        github.webhooks.PullRequestReopened,
        github.webhooks.PullRequestSynchronize,
    ],
) -> None:
    pr = await upsert_pull_request(session, event)
    if not pr:
        log.error("github.webhook.handle_pull_request.failed")
        return


@task("github.webhook.pull_request.opened")
async def pull_request_opened(
    ctx: JobContext,
    scope: str,
    action: str,
    payload: dict[str, Any],
    polar_context: PolarWorkerContext,
) -> None:
    with polar_context.to_execution_context():
        parsed = github.webhooks.parse_obj(scope, payload)
        if not isinstance(parsed, github.webhooks.PullRequestOpened):
            log.error("github.webhook.unexpected_type")
            raise Exception("unexpected webhook payload")

        async with AsyncSessionLocal() as session:
            await handle_pull_request(session, scope, action, parsed)


@task("github.webhook.pull_request.edited")
async def pull_request_edited(
    ctx: JobContext,
    scope: str,
    action: str,
    payload: dict[str, Any],
    polar_context: PolarWorkerContext,
) -> None:
    with polar_context.to_execution_context():
        parsed = github.webhooks.parse_obj(scope, payload)
        if not isinstance(parsed, github.webhooks.PullRequestEdited):
            log.error("github.webhook.unexpected_type")
            raise Exception("unexpected webhook payload")

        async with AsyncSessionLocal() as session:
            await handle_pull_request(session, scope, action, parsed)


@task("github.webhook.pull_request.closed")
async def pull_request_closed(
    ctx: JobContext,
    scope: str,
    action: str,
    payload: dict[str, Any],
    polar_context: PolarWorkerContext,
) -> None:
    with polar_context.to_execution_context():
        parsed = github.webhooks.parse_obj(scope, payload)
        if not isinstance(parsed, github.webhooks.PullRequestClosed):
            log.error("github.webhook.unexpected_type")
            raise Exception("unexpected webhook payload")

        async with AsyncSessionLocal() as session:
            await handle_pull_request(session, scope, action, parsed)


@task("github.webhook.pull_request.reopened")
async def pull_request_reopened(
    ctx: JobContext,
    scope: str,
    action: str,
    payload: dict[str, Any],
    polar_context: PolarWorkerContext,
) -> None:
    with polar_context.to_execution_context():
        parsed = github.webhooks.parse_obj(scope, payload)
        if not isinstance(parsed, github.webhooks.PullRequestReopened):
            log.error("github.webhook.unexpected_type")
            raise Exception("unexpected webhook payload")

        async with AsyncSessionLocal() as session:
            await handle_pull_request(session, scope, action, parsed)


@task("github.webhook.pull_request.synchronize")
async def pull_request_synchronize(
    ctx: JobContext,
    scope: str,
    action: str,
    payload: dict[str, Any],
    polar_context: PolarWorkerContext,
) -> None:
    with polar_context.to_execution_context():
        parsed = github.webhooks.parse_obj(scope, payload)
        if not isinstance(parsed, github.webhooks.PullRequestSynchronize):
            log.error("github.webhook.unexpected_type")
            raise Exception("unexpected webhook payload")

        async with AsyncSessionLocal() as session:
            await handle_pull_request(session, scope, action, parsed)


# ------------------------------------------------------------------------------
# INSTALLATION
# ------------------------------------------------------------------------------


@task("github.webhook.installation.created")
async def installation_created(
    ctx: JobContext,
    scope: str,
    action: str,
    payload: dict[str, Any],
    polar_context: PolarWorkerContext,
) -> None:
    with ExecutionContext(is_during_installation=True):
        event = github.webhooks.parse_obj(scope, payload)
        if not isinstance(event, github.webhooks.InstallationCreated):
            log.error("github.webhook.unexpected_type")
            raise Exception("unexpected webhook payload")

        async with AsyncSessionLocal() as session:
            await repositories_changed(session, event)


@task("github.webhook.installation.deleted")
async def installation_delete(
    ctx: JobContext,
    scope: str,
    action: str,
    payload: dict[str, Any],
    polar_context: PolarWorkerContext,
) -> None:
    with polar_context.to_execution_context():
        event = github.webhooks.parse_obj(scope, payload)
        if not isinstance(event, github.webhooks.InstallationDeleted):
            log.error("github.webhook.unexpected_type")
            raise Exception("unexpected webhook payload")

        async with AsyncSessionLocal() as session:
            org = await service.github_organization.get_by_external_id(
                session, event.installation.account.id
            )
            if not org:
                return
            await service.github_organization.remove(session, org.id)


@task("github.webhook.installation.suspend")
async def installation_suspend(
    ctx: JobContext,
    scope: str,
    action: str,
    payload: dict[str, Any],
    polar_context: PolarWorkerContext,
) -> None:
    with polar_context.to_execution_context():
        event = github.webhooks.parse_obj(scope, payload)
        if not isinstance(event, github.webhooks.InstallationSuspend):
            log.error("github.webhook.unexpected_type")
            raise Exception("unexpected webhook payload")

        async with AsyncSessionLocal() as session:
            await service.github_organization.suspend(
                session,
                event.installation.id,
                event.installation.suspended_by.id,
                event.installation.suspended_at,
                event.sender.id,
            )


@task("github.webhook.installation.unsuspend")
async def installation_unsuspend(
    ctx: JobContext,
    scope: str,
    action: str,
    payload: dict[str, Any],
    polar_context: PolarWorkerContext,
) -> None:
    with polar_context.to_execution_context():
        event = github.webhooks.parse_obj(scope, payload)
        if not isinstance(event, github.webhooks.InstallationUnsuspend):
            log.error("github.webhook.unexpected_type")
            raise Exception("unexpected webhook payload")

        async with AsyncSessionLocal() as session:
            await service.github_organization.unsuspend(session, event.installation.id)
