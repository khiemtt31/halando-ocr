from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from app.api.deps import get_current_principal, get_session
from app.core.security import Principal
from app.repositories.users import upsert_user
from app.schemas.auth import MeResponse

router = APIRouter(tags=["auth"])


@router.get("/me", response_model=MeResponse)
async def me(
    request: Request,
    principal: Principal = Depends(get_current_principal),
    session=Depends(get_session),
) -> MeResponse:
    user = await upsert_user(session, principal)
    await session.commit()
    return MeResponse(
        sub=principal.sub,
        email=principal.email,
        name=principal.name,
        tenant_id=principal.tenant_id,
        roles=principal.roles,
        user_id=user.id,
        status=user.status,
    )
