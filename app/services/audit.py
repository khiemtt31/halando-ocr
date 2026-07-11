from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import Principal
from app.repositories.audit import create_audit_event


async def record_audit_event(
    session: AsyncSession,
    *,
    principal: Principal | None,
    action: str,
    resource_type: str,
    resource_id: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    metadata_json: dict | None = None,
) -> None:
    await create_audit_event(
        session,
        actor_sub=principal.sub if principal else None,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        ip_address=ip_address,
        user_agent=user_agent,
        metadata_json=metadata_json,
    )
    await session.commit()
