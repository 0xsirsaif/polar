from typing import Sequence
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from polar.auth.dependencies import Auth
from .schemas import BackofficePledgeRead
from polar.kit.extensions.sqlalchemy import sql
from polar.models.pledge import Pledge
from polar.postgres import AsyncSession, get_db_session

from polar.pledge.schemas import PledgeRead
from polar.pledge.service import pledge as pledge_service

from .pledge_service import bo_pledges_service


router = APIRouter(tags=["backoffice"], prefix="/backoffice")


@router.get("/pledges", response_model=list[BackofficePledgeRead])
async def pledges(
    auth: Auth = Depends(Auth.backoffice_user),
    session: AsyncSession = Depends(get_db_session),
) -> list[BackofficePledgeRead]:
    return await bo_pledges_service.list_pledges(session, customers=True)


@router.get("/pledges/non_customers", response_model=list[BackofficePledgeRead])
async def pledges_non_customers(
    auth: Auth = Depends(Auth.backoffice_user),
    session: AsyncSession = Depends(get_db_session),
) -> list[BackofficePledgeRead]:
    return await bo_pledges_service.list_pledges(session, customers=False)


async def get_pledge(session: AsyncSession, pledge_id: UUID) -> BackofficePledgeRead:
    pledge = await pledge_service.get_with_loaded(session, pledge_id)
    if not pledge:
        raise HTTPException(
            status_code=404,
            detail="Pledge not found",
        )
    return BackofficePledgeRead.from_db(pledge)


@router.post("/pledges/approve/{pledge_id}", response_model=BackofficePledgeRead)
async def pledge_approve(
    pledge_id: UUID,
    auth: Auth = Depends(Auth.backoffice_user),
    session: AsyncSession = Depends(get_db_session),
) -> BackofficePledgeRead:
    await pledge_service.transfer(session, pledge_id)
    return await get_pledge(session, pledge_id)


@router.post("/pledges/mark_pending/{pledge_id}", response_model=BackofficePledgeRead)
async def pledge_mark_pending(
    pledge_id: UUID,
    auth: Auth = Depends(Auth.backoffice_user),
    session: AsyncSession = Depends(get_db_session),
) -> BackofficePledgeRead:
    await pledge_service.mark_pending_by_pledge_id(session, pledge_id)
    return await get_pledge(session, pledge_id)