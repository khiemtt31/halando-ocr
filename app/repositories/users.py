from __future__ import annotations

from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import Principal
from app.core.time import utcnow
from app.models.user import AppUser


async def upsert_user(session: AsyncSession, principal: Principal) -> AppUser:
    result = await session.scalars(select(AppUser).where(AppUser.local_sub == principal.sub))
    user = result.first()
    now = utcnow()
    if user is None:
        user = AppUser(
            id=str(uuid4()),
            local_sub=principal.sub,
            email=principal.email,
            display_name=principal.name,
            status="active",
            created_at=now,
            updated_at=now,
        )
        session.add(user)
    else:
        user.email = principal.email
        user.display_name = principal.name
        user.status = "active"
        user.updated_at = now
    await session.flush()
    return user
