from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from uuid import uuid4

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.errors import APIError
from app.core.security import Principal, create_signed_token, decode_signed_token
from app.core.time import utcnow
from app.models.document import Document
from app.repositories.documents import create_document, update_document_status
from app.repositories.jobs import ensure_job
from app.repositories.users import upsert_user
from app.services.storage import StorageBackend

SUPPORTED_PDF_MIME_TYPES = {"application/pdf"}
SUPPORTED_IMAGE_MIME_TYPES = {"image/png", "image/jpeg", "image/jpg", "image/tiff", "image/webp"}


@dataclass(slots=True)
class UploadIntent:
    document_id: str
    upload_url: str
    storage_key: str
    expires_in_seconds: int


def sanitize_filename(filename: str) -> str:
    name = Path(filename).name.strip() or "document"
    cleaned = [ch if ch.isalnum() or ch in {".", "-", "_"} else "_" for ch in name]
    return "".join(cleaned)[:180] or "document"


def guess_source_type(mime_type: str, filename: str) -> str:
    normalized = mime_type.lower().split(";")[0].strip()
    if normalized in SUPPORTED_PDF_MIME_TYPES or filename.lower().endswith(".pdf"):
        return "pdf"
    if normalized in SUPPORTED_IMAGE_MIME_TYPES:
        return "image"
    raise APIError("DOCUMENT_UNSUPPORTED_TYPE", f"Unsupported MIME type: {mime_type}", 415)


def validate_upload_size(size_bytes: int, settings: Settings) -> None:
    if size_bytes <= 0:
        raise APIError("VALIDATION_ERROR", "File size must be greater than zero.", 422)
    if size_bytes > settings.max_upload_size_bytes:
        raise APIError("DOCUMENT_TOO_LARGE", "Uploaded file exceeds the maximum allowed size.", 413)


def build_document_storage_key(settings: Settings, principal: Principal, document_id: str, filename: str) -> str:
    safe_name = sanitize_filename(filename)
    return (
        f"tenants/{principal.tenant_id or settings.default_tenant_id}/users/{principal.sub}"
        f"/documents/{document_id}/original/{safe_name}"
    )


def build_ocr_storage_key(settings: Settings, principal: Principal, document_id: str) -> str:
    return f"tenants/{principal.tenant_id or settings.default_tenant_id}/users/{principal.sub}/documents/{document_id}/ocr/output.pdf"


def build_upload_intent_token(
    settings: Settings,
    principal: Principal,
    *,
    document_id: str,
    storage_key: str,
    original_filename: str,
    mime_type: str,
    size_bytes: int,
    sha256_hex: str,
    language_hint: str | None,
) -> str:
    return create_signed_token(
        {
            "kind": "document_upload",
            "document_id": document_id,
            "owner_sub": principal.sub,
            "tenant_id": principal.tenant_id or settings.default_tenant_id,
            "storage_key": storage_key,
            "original_filename": original_filename,
            "mime_type": mime_type,
            "size_bytes": size_bytes,
            "sha256": sha256_hex,
            "language_hint": language_hint,
        },
        settings.secret_key,
        settings.upload_url_ttl_seconds,
    )


def decode_upload_intent_token(token: str, settings: Settings) -> dict[str, object]:
    claims = decode_signed_token(token, settings.secret_key)
    if claims.get("kind") != "document_upload":
        raise APIError("VALIDATION_ERROR", "Invalid upload token.", 422)
    return claims


async def create_upload_intent(
    session: AsyncSession,
    request: Request,
    principal: Principal,
    settings: Settings,
    *,
    filename: str,
    mime_type: str,
    size_bytes: int,
    sha256_hex: str,
    language_hint: str | None,
) -> UploadIntent:
    validate_upload_size(size_bytes, settings)
    source_type = guess_source_type(mime_type, filename)
    document_id = str(uuid4())
    storage_key = build_document_storage_key(settings, principal, document_id, filename)
    ocr_key = build_ocr_storage_key(settings, principal, document_id)

    await upsert_user(session, principal)
    document = await create_document(
        session,
        id=document_id,
        owner_sub=principal.sub,
        tenant_id=principal.tenant_id or settings.default_tenant_id,
        original_filename=sanitize_filename(filename),
        mime_type=mime_type,
        size_bytes=size_bytes,
        sha256=sha256_hex,
        source_type=source_type,
        status="uploaded",
        language_hint=language_hint,
        page_count=None,
        storage_original_key=storage_key,
        storage_ocr_pdf_key=ocr_key,
        created_at=utcnow(),
        updated_at=utcnow(),
    )
    await session.commit()
    token = build_upload_intent_token(
        settings,
        principal,
        document_id=document.id,
        storage_key=storage_key,
        original_filename=document.original_filename,
        mime_type=mime_type,
        size_bytes=size_bytes,
        sha256_hex=sha256_hex,
        language_hint=language_hint,
    )
    upload_url = str(request.url_for("receive_upload", upload_token=token))
    return UploadIntent(document_id=document.id, upload_url=upload_url, storage_key=storage_key, expires_in_seconds=settings.upload_url_ttl_seconds)


async def save_direct_upload(
    session: AsyncSession,
    storage: StorageBackend,
    principal: Principal,
    settings: Settings,
    *,
    filename: str,
    mime_type: str,
    data: bytes,
    language_hint: str | None,
) -> Document:
    validate_upload_size(len(data), settings)
    source_type = guess_source_type(mime_type, filename)
    sha256_hex = sha256(data).hexdigest()
    await upsert_user(session, principal)
    document_id = str(uuid4())
    storage_key = build_document_storage_key(settings, principal, document_id, filename)
    ocr_key = build_ocr_storage_key(settings, principal, document_id)
    await storage.save_bytes(storage_key, data, mime_type)
    document = await create_document(
        session,
        id=document_id,
        owner_sub=principal.sub,
        tenant_id=principal.tenant_id or settings.default_tenant_id,
        original_filename=sanitize_filename(filename),
        mime_type=mime_type,
        size_bytes=len(data),
        sha256=sha256_hex,
        source_type=source_type,
        status="uploaded",
        language_hint=language_hint,
        page_count=None,
        storage_original_key=storage_key,
        storage_ocr_pdf_key=ocr_key,
        created_at=utcnow(),
        updated_at=utcnow(),
    )
    return document


async def create_or_resume_ocr_job(session: AsyncSession, document: Document, *, engine: str = "pdfplumber"):
    return await ensure_job(session, document, engine=engine)


async def finalize_upload(session: AsyncSession, storage: StorageBackend, document: Document) -> Document:
    if not await storage.exists(document.storage_original_key):
        raise APIError("STORAGE_FILE_MISSING", "Uploaded file is not available in local storage.", 409)
    if document.status == "deleted":
        raise APIError("DOCUMENT_NOT_FOUND", "Document not found or access denied.", 404)
    if document.status == "failed":
        document.status = "uploaded"
    await update_document_status(session, document, "uploaded")
    return document
