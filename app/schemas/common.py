from __future__ import annotations

from pydantic import BaseModel


class ErrorPayload(BaseModel):
    code: str
    message: str
    request_id: str


class ErrorResponse(BaseModel):
    error: ErrorPayload


class PageResponse(BaseModel):
    limit: int
    offset: int
    total: int


class MessageResponse(BaseModel):
    message: str
