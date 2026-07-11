from __future__ import annotations

from typing import Any
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.time import utcnow
from app.models.audit_event import AuditEvent


async def create_audit_event(
    session: AsyncSession,
    *,
    actor_sub: str | None,
    action: str,
    resource_type: str,
    resource_id: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    metadata_json: dict[str, Any] | None = None,
) -> AuditEvent:
    event = AuditEvent(
        id=str(uuid4()),
        actor_sub=actor_sub,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        ip_address=ip_address,
        user_agent=user_agent,
        metadata_json=metadata_json,
        created_at=utcnow(),
    )
    session.add(event)
    await session.flush()
    return event


async def list_audit_events(session: AsyncSession, *, limit: int = 20, offset: int = 0) -> tuple[list[AuditEvent], int]:
    items = list(
        (
            await session.scalars(
                select(AuditEvent).order_by(AuditEvent.created_at.desc()).offset(offset).limit(limit)
            )
        ).all()
    )
    total = int((await session.execute(select(func.count()).select_from(AuditEvent))).scalar_one())
    return items, total
