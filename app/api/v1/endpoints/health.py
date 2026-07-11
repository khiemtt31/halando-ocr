from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session

router = APIRouter(tags=["public"])


@router.get("/health")
async def health(request: Request) -> dict[str, str]:
    settings = request.app.state.runtime.settings
    return {"status": "ok", "app_name": settings.app_name, "environment": settings.app_env}


@router.get("/ready")
async def ready(session: AsyncSession = Depends(get_session)) -> dict[str, str]:
    await session.execute(text("SELECT 1"))
    return {"status": "ready"}
