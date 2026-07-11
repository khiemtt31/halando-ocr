from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.common import PageResponse


class JobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    document_id: str
    status: str
    engine: str
    progress: int
    attempt_count: int
    max_attempts: int
    error_code: str | None = None
    error_message: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class JobListResponse(PageResponse):
    items: list[JobRead]
