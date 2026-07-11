from __future__ import annotations

from collections.abc import AsyncIterator, Callable

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.errors import APIError
from app.core.security import Principal
from app.services.storage import StorageBackend

bearer_scheme = HTTPBearer(auto_error=False)


async def get_settings(request: Request) -> Settings:
    return request.app.state.runtime.settings


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    sessionmaker = request.app.state.runtime.sessionmaker
    async with sessionmaker() as session:
        yield session


async def get_storage(request: Request) -> StorageBackend:
    return request.app.state.runtime.storage


async def get_current_principal(
    request: Request,
    _credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> Principal:
    return await request.app.state.runtime.auth.resolve_principal(request)


def require_roles(*required_roles: str) -> Callable[..., object]:
    async def dependency(principal: Principal = Depends(get_current_principal)) -> Principal:
        missing = set(required_roles) - set(principal.roles)
        if missing:
            raise APIError(
                "AUTH_FORBIDDEN",
                f"Missing required role(s): {', '.join(sorted(missing))}",
                403,
            )
        return principal

    return dependency
