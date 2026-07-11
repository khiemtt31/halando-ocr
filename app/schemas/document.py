from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator

from app.schemas.common import PageResponse


class DocumentUploadUrlRequest(BaseModel):
    filename: str
    mime_type: str
    size_bytes: int
    sha256: str
    language_hint: str | None = None

    @field_validator("sha256")
    @classmethod
    def validate_sha256(cls, value: str) -> str:
        normalized = value.lower().strip()
        if len(normalized) != 64 or any(ch not in "0123456789abcdef" for ch in normalized):
            raise ValueError("sha256 must be a 64-character hexadecimal string")
        return normalized


class DocumentUploadUrlResponse(BaseModel):
    document_id: str
    upload_url: str
    storage_key: str
    expires_in_seconds: int


class DocumentCreateResponse(BaseModel):
    document_id: str
    job_id: str


class CompleteUploadResponse(BaseModel):
    document_id: str
    job_id: str
    status: str


class DocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    owner_sub: str
    tenant_id: str
    original_filename: str
    mime_type: str
    size_bytes: int
    sha256: str
    source_type: str
    status: str
    language_hint: str | None = None
    page_count: int | None = None
    storage_original_key: str
    storage_ocr_pdf_key: str | None = None
    created_at: datetime
    updated_at: datetime


class DocumentListResponse(PageResponse):
    items: list[DocumentRead]


class DocumentPageRead(BaseModel):
    page_number: int
    text_content: str | None = None
    confidence: float | None = None
    width: int | None = None
    height: int | None = None


class DocumentTextResponse(BaseModel):
    document_id: str
    original_filename: str
    page_count: int | None = None
    text: str
    pages: list[DocumentPageRead]


class DownloadUrlResponse(BaseModel):
    url: str
    expires_in_seconds: int


class UploadConfirmationResponse(BaseModel):
    document_id: str
    status: str
