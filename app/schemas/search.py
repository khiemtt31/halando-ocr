from __future__ import annotations

from pydantic import BaseModel

from app.schemas.common import PageResponse


class SearchHit(BaseModel):
    document_id: str
    document_filename: str
    page_number: int
    snippet: str
    matched_text: str
    status: str


class SearchResponse(PageResponse):
    items: list[SearchHit]
