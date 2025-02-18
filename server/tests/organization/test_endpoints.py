from datetime import datetime

import pytest
from httpx import AsyncClient

from polar.app import app
from polar.config import settings
from polar.models.organization import Organization
from polar.models.user import User
from polar.models.user_organization import UserOrganization
from polar.postgres import AsyncSession


@pytest.mark.asyncio
async def test_get_organization_no_member_old_api(
    organization: Organization,
    auth_jwt: str,
) -> None:
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get(
            "/api/v1/github/" + organization.name,
            cookies={settings.AUTH_COOKIE_KEY: auth_jwt},
        )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_organization_member_old_api(
    organization: Organization,
    user_organization: UserOrganization,  # makes User a member of Organization
    auth_jwt: str,
) -> None:
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get(
            "/api/v1/github/" + organization.name,
            cookies={settings.AUTH_COOKIE_KEY: auth_jwt},
        )

    assert response.status_code == 200
    assert response.json()["id"] == str(organization.id)


@pytest.mark.asyncio
async def test_get_organization_deleted_old_api(
    session: AsyncSession,
    organization: Organization,
    user_organization: UserOrganization,  # makes User a member of Organization
    auth_jwt: str,
) -> None:
    # soft-delete the organization
    organization.deleted_at = datetime.utcnow()
    await organization.save(session)

    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get(
            "/api/v1/github/" + organization.name,
            cookies={settings.AUTH_COOKIE_KEY: auth_jwt},
        )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_organization(
    organization: Organization,
    auth_jwt: str,
) -> None:
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get(
            f"/api/v1/organizations/{organization.id}",
            cookies={settings.AUTH_COOKIE_KEY: auth_jwt},
        )

    assert response.status_code == 200
    assert response.json()["id"] == str(organization.id)


@pytest.mark.asyncio
async def test_list_organization_member(
    organization: Organization,
    user_organization: UserOrganization,  # makes User a member of Organization
    auth_jwt: str,
) -> None:
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get(
            "/api/v1/organizations",
            cookies={settings.AUTH_COOKIE_KEY: auth_jwt},
        )

    assert response.status_code == 200
    assert response.json()["items"][0]["id"] == str(organization.id)


@pytest.mark.asyncio
async def test_organization_lookup_not_found(
    organization: Organization,
    auth_jwt: str,
) -> None:
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get(
            "/api/v1/organizations/lookup?platform=github&organization_name=foobar",
            cookies={settings.AUTH_COOKIE_KEY: auth_jwt},
        )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_organization_lookup(
    organization: Organization,
    auth_jwt: str,
) -> None:
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get(
            f"/api/v1/organizations/lookup?platform=github&organization_name={organization.name}",
            cookies={settings.AUTH_COOKIE_KEY: auth_jwt},
        )

    assert response.status_code == 200
    assert response.json()["id"] == str(organization.id)


@pytest.mark.asyncio
async def test_organization_search(
    organization: Organization,
    auth_jwt: str,
) -> None:
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get(
            f"/api/v1/organizations/search?platform=github&organization_name={organization.name}",
            cookies={settings.AUTH_COOKIE_KEY: auth_jwt},
        )

    assert response.status_code == 200
    assert response.json()["items"][0]["id"] == str(organization.id)


@pytest.mark.asyncio
async def test_organization_search_no_matches(
    organization: Organization,
    auth_jwt: str,
) -> None:
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get(
            "/api/v1/organizations/search?platform=github&organization_name=foobar",
            cookies={settings.AUTH_COOKIE_KEY: auth_jwt},
        )

    assert response.status_code == 200
    assert response.json()["items"] == []


@pytest.mark.asyncio
async def test_get_organization_deleted(
    session: AsyncSession,
    organization: Organization,
    user_organization: UserOrganization,  # makes User a member of Organization
    auth_jwt: str,
) -> None:
    # soft-delete the organization
    organization.deleted_at = datetime.utcnow()
    await organization.save(session)

    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get(
            f"/api/v1/organizations/{organization.id}",
            cookies={settings.AUTH_COOKIE_KEY: auth_jwt},
        )

    assert response.status_code == 404
