from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from app import models as _models  # noqa: F401
from app.core.auth import AuthProvider, Principal, build_auth_provider
from app.core.config import Settings
from app.db.base import Base
from app.db.session import build_engine, build_sessionmaker
from app.repositories.users import upsert_user
from app.services.storage import LocalStorageBackend, StorageBackend


@dataclass(slots=True)
class Runtime:
    settings: Settings
    engine: AsyncEngine
    sessionmaker: async_sessionmaker[AsyncSession]
    auth: AuthProvider
    storage: StorageBackend


def _ensure_paths(settings: Settings) -> None:
    settings.local_storage_root.mkdir(parents=True, exist_ok=True)
    url = make_url(settings.database_url)
    if url.drivername.startswith("sqlite") and url.database and url.database != ":memory:":
        Path(url.database).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)


def build_runtime(settings: Settings) -> Runtime:
    _ensure_paths(settings)
    engine = build_engine(settings)
    sessionmaker = build_sessionmaker(engine)
    auth = build_auth_provider(settings)
    storage = LocalStorageBackend(settings.local_storage_root)
    return Runtime(settings=settings, engine=engine, sessionmaker=sessionmaker, auth=auth, storage=storage)


async def init_database(runtime: Runtime) -> None:
    async with runtime.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def seed_database(runtime: Runtime) -> None:
    if not runtime.settings.seeded_account_enabled:
        return
    principal = Principal(
        sub=runtime.settings.seeded_account_sub,
        email=runtime.settings.seeded_account_email,
        name=runtime.settings.seeded_account_name,
        tenant_id=runtime.settings.default_tenant_id,
        roles=[],
        claims={"mode": "seed"},
    )
    async with runtime.sessionmaker() as session:
        await upsert_user(session, principal)
        await session.commit()


async def close_runtime(runtime: Runtime) -> None:
    await runtime.auth.aclose()
    await runtime.engine.dispose()
