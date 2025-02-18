from uuid import UUID
import structlog
from polar.integrations.github import service
from polar.integrations.github.client import get_app_installation_client

from polar.worker import JobContext, PolarWorkerContext, enqueue_job, interval, task
from polar.postgres import AsyncSessionLocal

from .utils import get_organization_and_repo
from ..service.issue import github_issue
from ..service.api import github_api
from polar.organization.service import organization as organization_service

log = structlog.get_logger()


@task("github.issue.sync")
async def issue_sync(
    ctx: JobContext,
    issue_id: UUID,
    polar_context: PolarWorkerContext,
    crawl_with_installation_id: int
    | None = None,  # Override which installation to use when crawling
) -> None:
    with polar_context.to_execution_context():
        async with AsyncSessionLocal() as session:
            issue = await github_issue.get(session, issue_id)
            if not issue or not issue.organization_id or not issue.repository_id:
                log.warning(
                    "github.issue.sync",
                    error="issue not found",
                    issue_id=issue_id,
                )
                return

            organization, repository = await get_organization_and_repo(
                session, issue.organization_id, issue.repository_id
            )

            await github_issue.sync_issue(
                session,
                org=organization,
                repo=repository,
                issue=issue,
                crawl_with_installation_id=crawl_with_installation_id,
            )


@task("github.issue.sync.issue_references")
async def issue_sync_issue_references(
    ctx: JobContext,
    issue_id: UUID,
    polar_context: PolarWorkerContext,
    crawl_with_installation_id: int
    | None = None,  # Override which installation to use when crawling
) -> None:
    with polar_context.to_execution_context():
        async with AsyncSessionLocal() as session:
            issue = await github_issue.get(session, issue_id)
            if not issue or not issue.organization_id or not issue.repository_id:
                log.warning(
                    "github.issue.sync.issue_references",
                    error="issue not found",
                    issue_id=issue_id,
                )
                return

            organization, repository = await get_organization_and_repo(
                session, issue.organization_id, issue.repository_id
            )

            await service.github_reference.sync_issue_references(
                session,
                org=organization,
                repo=repository,
                issue=issue,
                crawl_with_installation_id=crawl_with_installation_id,
            )


@task("github.issue.sync.issue_dependencies")
async def issue_sync_issue_dependencies(
    ctx: JobContext,
    issue_id: UUID,
    polar_context: PolarWorkerContext,
) -> None:
    with polar_context.to_execution_context():
        async with AsyncSessionLocal() as session:
            issue = await github_issue.get(session, issue_id)
            if not issue or not issue.organization_id or not issue.repository_id:
                log.warning(
                    "github.issue.sync.issue_dependencies",
                    error="issue not found",
                    issue_id=issue_id,
                )
                return

            organization, repository = await get_organization_and_repo(
                session, issue.organization_id, issue.repository_id
            )

            await service.github_dependency.sync_issue_dependencies(
                session,
                org=organization,
                repo=repository,
                issue=issue,
            )


@interval(
    minute={2, 7, 12, 17, 22, 27, 32, 37, 42, 47, 52, 57},
    second=0,
)
async def cron_refresh_issues(ctx: JobContext) -> None:
    async with AsyncSessionLocal() as session:
        orgs = await organization_service.list_installed(session)
        for org in orgs:
            client = get_app_installation_client(org.installation_id)
            try:
                rate_limit = await github_api.get_rate_limit(client)
            except Exception as e:
                log.info(
                    "failed to get rate limit, treating it as no remaining",
                    org_name=org.name,
                    err=e,
                )
                continue

            if rate_limit.remaining < 1000:
                log.info(
                    "github.issue.sync.cron_refresh_issues.rate_limit_almost_exhausted",
                    org_name=org.name,
                    rate_limit_remaining=rate_limit.remaining,
                )
                continue

            issues = await github_issue.list_issues_to_crawl_issue(session, org)

            log.info(
                "github.issue.sync.cron_refresh_issues",
                org_name=org.name,
                found_count=len(issues),
                rate_limit_remaining=rate_limit.remaining,
            )

            for issue in issues:
                await enqueue_job("github.issue.sync", issue.id)


@interval(
    minute={0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55},
    second=0,
)
async def cron_refresh_issue_timelines(ctx: JobContext) -> None:
    async with AsyncSessionLocal() as session:
        orgs = await organization_service.list_installed(session)
        for org in orgs:
            client = get_app_installation_client(org.installation_id)

            try:
                rate_limit = await github_api.get_rate_limit(client)
            except Exception as e:
                log.info(
                    "failed to get rate limit, treating it as no remaining",
                    org_name=org.name,
                    err=e,
                )
                continue

            if rate_limit.remaining < 1000:
                log.info(
                    "github.issue.sync.cron_refresh_issue_timelines.rate_limit_almost_exhausted",
                    org_name=org.name,
                    rate_limit_remaining=rate_limit.remaining,
                )
                continue

            issues = await github_issue.list_issues_to_crawl_timeline(session, org)

            log.info(
                "github.issue.sync.cron_refresh_issue_timelines",
                org_name=org.name,
                found_count=len(issues),
                rate_limit_remaining=rate_limit.remaining,
            )

            for issue in issues:
                await enqueue_job("github.issue.sync.issue_references", issue.id)
