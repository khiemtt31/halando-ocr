from __future__ import annotations

from sqlalchemy import event
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import Settings


def build_engine(settings: Settings) -> AsyncEngine:
    engine_kwargs: dict[str, object] = {
        "echo": False,
        "future": True,
        "pool_pre_ping": True,
    }
    url = make_url(settings.database_url)
    if url.drivername.startswith("sqlite"):
        engine_kwargs["poolclass"] = NullPool

    engine = create_async_engine(settings.database_url, **engine_kwargs)

    if url.drivername.startswith("sqlite"):

        @event.listens_for(engine.sync_engine, "connect")
        def _set_sqlite_pragma(dbapi_connection, connection_record) -> None:  # type: ignore[no-untyped-def]
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return engine


def build_sessionmaker(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False)
