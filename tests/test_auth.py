from __future__ import annotations

import pytest
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.core.config import Settings
from app.main import create_app
from app.models.user import AppUser


@pytest.mark.asyncio
async def test_seeded_account_is_created_in_sqlite(tmp_path) -> None:
    settings = Settings(
        app_env="local",
        auth_provider="local",
        database_url=f"sqlite+aiosqlite:///{tmp_path / 'dococr.db'}",
        local_storage_root=tmp_path / "storage",
        auto_create_schema=True,
    )
    app = create_app(settings)

    async with LifespanManager(app):
        async with app.state.runtime.sessionmaker() as session:
            user = (
                await session.scalars(
                    select(AppUser).where(AppUser.local_sub == settings.seeded_account_sub),
                )
            ).first()

    assert user is not None
    assert user.email == settings.seeded_account_email
    assert user.display_name == settings.seeded_account_name


@pytest.mark.asyncio
async def test_keycloak_auth_config_and_missing_bearer_rejection(tmp_path) -> None:
    settings = Settings(
        app_env="local",
        auth_provider="keycloak",
        database_url=f"sqlite+aiosqlite:///{tmp_path / 'dococr.db'}",
        local_storage_root=tmp_path / "storage",
        keycloak_server_url="http://keycloak:8080",
        keycloak_public_server_url="http://localhost:8080",
        auto_create_schema=True,
    )
    app = create_app(settings)

    async with (
        LifespanManager(app),
        AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client,
    ):
        config = await client.get("/api/v1/auth/config")
        me = await client.get("/api/v1/me")

    assert config.status_code == 200
    assert config.json()["provider"] == "keycloak"
    assert config.json()["issuer_url"] == "http://localhost:8080/realms/halando"
    assert config.json()["seeded_account"]["username"] == "demo"
    assert me.status_code == 401
    assert me.json()["error"]["code"] == "AUTH_UNAUTHORIZED"
