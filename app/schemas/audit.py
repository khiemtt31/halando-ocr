from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.common import PageResponse


class AuditEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    actor_sub: str | None = None
    action: str
    resource_type: str
    resource_id: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    metadata_json: dict | None = None
    created_at: datetime


class AuditEventListResponse(PageResponse):
    items: list[AuditEventRead]
