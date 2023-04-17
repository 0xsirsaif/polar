from __future__ import annotations
from uuid import UUID


import structlog
from polar.backoffice.schemas import BackofficePledgeRead
from polar.kit.extensions.sqlalchemy import sql
from sqlalchemy.orm import (
    joinedload,
)
from polar.models.issue import Issue
from polar.models.organization import Organization

from polar.models.pledge import Pledge

from polar.models.user import User

from polar.models.account import Account
from polar.postgres import AsyncSession
from polar.enums import AccountType
from polar.integrations.stripe.service import stripe


log = structlog.get_logger()


class BackofficePledgeService:
    async def list_pledges(
        self, session: AsyncSession, customers: bool | None = None
    ) -> list[BackofficePledgeRead]:
        stmt = sql.select(Pledge).options(
            joinedload(Pledge.organization),
            joinedload(Pledge.user),
            joinedload(Pledge.issue).joinedload(Issue.organization),
            joinedload(Pledge.issue).joinedload(Issue.repository),
        )

        # Pledges to customers
        if customers:
            stmt = stmt.where(
                Pledge.issue.has(
                    Issue.organization.has(Organization.onboarded_at.is_not(None))
                )
            )

            # Pledges to non customers
        if not customers:
            stmt = stmt.where(
                Pledge.issue.has(
                    Issue.organization.has(Organization.onboarded_at.is_(None))
                )
            )

        res = await session.execute(stmt)
        pledges = res.scalars().unique().all()
        return [BackofficePledgeRead.from_db(p) for p in pledges]


bo_pledges_service = BackofficePledgeService()