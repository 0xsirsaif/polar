from typing import Any, Sequence, Union

import structlog
from githubkit import GitHub

from polar.enums import Platforms
from polar.models import Organization, PullRequest, Repository
from polar.postgres import AsyncSession
from polar.pull_request.hooks import PullRequestHook, pull_request_upserted
from polar.pull_request.schemas import FullPullRequestCreate, MinimalPullRequestCreate
from polar.pull_request.service import PullRequestService, full_pull_request

from .. import client as github

log = structlog.get_logger()


class GithubPullRequestService(PullRequestService):
    async def get_by_external_id(
        self, session: AsyncSession, external_id: int
    ) -> PullRequest | None:
        return await self.get_by_platform(session, Platforms.github, external_id)

    async def store_simple(
        self,
        session: AsyncSession,
        *,
        data: github.rest.PullRequestSimple,
        organization: Organization,
        repository: Repository,
    ) -> PullRequest:
        records = await self.store_many_simple(
            session,
            data=[data],
            organization=organization,
            repository=repository,
        )
        return records[0]

    async def store_many_simple(
        self,
        session: AsyncSession,
        *,
        data: Sequence[github.rest.PullRequestSimple],
        organization: Organization,
        repository: Repository,
    ) -> Sequence[PullRequest]:
        def parse(pr: github.rest.PullRequestSimple) -> MinimalPullRequestCreate:
            return MinimalPullRequestCreate.minimal_pull_request_from_github(
                pr,
                organization_id=organization.id,
                repository_id=repository.id,
            )

        create_schemas = [parse(pr) for pr in data]
        if not create_schemas:
            log.warning(
                "github.pull_request",
                error="no pull requests to store",
                organization_id=organization.id,
                repository_id=repository.id,
            )
            return []

        res = await self.upsert_many(
            session,
            create_schemas,
            constraints=[PullRequest.external_id],
            mutable_keys=MinimalPullRequestCreate.__mutable_keys__,
        )

        for r in res:
            await pull_request_upserted.call(PullRequestHook(session, r))

        return res

    async def store_full(
        self,
        session: AsyncSession,
        data: Union[
            github.rest.PullRequest, github.webhooks.PullRequestOpenedPropPullRequest
        ],
        organization: Organization,
        repository: Repository,
    ) -> PullRequest:
        records = await self.store_many_full(
            session,
            [data],
            organization=organization,
            repository=repository,
        )
        return records[0]

    async def store_many_full(
        self,
        session: AsyncSession,
        data: Sequence[
            Union[
                github.rest.PullRequest,
                github.webhooks.PullRequestOpenedPropPullRequest,
            ],
        ],
        organization: Organization,
        repository: Repository,
    ) -> Sequence[PullRequest]:
        def parse(
            pr: Union[
                github.rest.PullRequest,
                github.webhooks.PullRequestOpenedPropPullRequest,
            ],
        ) -> FullPullRequestCreate:
            return FullPullRequestCreate.full_pull_request_from_github(
                pr,
                organization_id=organization.id,
                repository_id=repository.id,
            )

        create_schemas = [parse(pr) for pr in data]
        if not create_schemas:
            log.warning(
                "github.pull_request",
                error="no pull requests to store",
                organization_id=organization.id,
                repository_id=repository.id,
            )
            return []

        res = await full_pull_request.upsert_many(
            session,
            create_schemas,
            constraints=[PullRequest.external_id],
            mutable_keys=FullPullRequestCreate.__mutable_keys__,
        )

        for r in res:
            await pull_request_upserted.call(PullRequestHook(session, r))

        return res

    async def sync_pull_request(
        self,
        session: AsyncSession,
        organization: Organization,
        repository: Repository,
        number: int,
        client: GitHub[Any],
    ) -> PullRequest | None:
        gh_pull = await client.rest.pulls.async_get(
            owner=organization.name, repo=repository.name, pull_number=number
        )
        if not gh_pull:
            return None

        pull = await self.store_full(
            session, gh_pull.parsed_data, organization, repository
        )

        return pull


github_pull_request = GithubPullRequestService(PullRequest)
