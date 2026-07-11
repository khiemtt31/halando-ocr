from __future__ import annotations

import io
from dataclasses import asdict
from hashlib import sha256
from mimetypes import guess_type
from urllib.parse import quote

from fastapi import APIRouter, Depends, File, Form, Query, Request, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy import delete

from app.api.deps import get_session, get_settings, get_storage, require_roles
from app.core.config import Settings
from app.core.errors import APIError
from app.core.security import Principal
from app.models.document import Document
from app.models.document_page import DocumentPage
from app.models.search import DocumentSearch
from app.repositories.documents import get_document, list_documents, mark_document_deleted
from app.repositories.pages import get_document_pages
from app.schemas.common import MessageResponse
from app.schemas.document import (
    CompleteUploadResponse,
    DocumentCreateResponse,
    DocumentListResponse,
    DocumentPageRead,
    DocumentRead,
    DocumentTextResponse,
    DocumentUploadUrlRequest,
    DocumentUploadUrlResponse,
    DownloadUrlResponse,
    UploadConfirmationResponse,
)
from app.schemas.job import JobRead
from app.services.audit import record_audit_event
from app.services.documents import (
    create_or_resume_ocr_job,
    create_upload_intent,
    decode_upload_intent_token,
    finalize_upload,
    save_direct_upload,
)

router = APIRouter(tags=["documents"])


def _document_response(document: Document) -> DocumentRead:
    return DocumentRead.model_validate(document)


def _job_response(job) -> JobRead:
    return JobRead.model_validate(job)


def _resolve_upload_mime(file: UploadFile) -> str:
    if file.content_type:
        return file.content_type
    guessed, _ = guess_type(file.filename or "")
    return guessed or "application/octet-stream"


async def _load_document_or_404(session, principal: Principal, document_id: str) -> Document:
    document = await get_document(session, document_id, owner_sub=principal.sub, admin=principal.is_admin)
    if document is None:
        raise APIError("DOCUMENT_NOT_FOUND", "Document not found or access denied.", 404)
    return document


def _build_download_url(request: Request, document: Document, *, ocr: bool = False) -> str:
    route_name = "download_document_ocr" if ocr else "download_document"
    return str(request.url_for(route_name, document_id=document.id))


@router.post(
    "/documents/upload-url",
    response_model=DocumentUploadUrlResponse,
    status_code=201,
)
async def create_upload_url(
    request: Request,
    payload: DocumentUploadUrlRequest,
    session=Depends(get_session),
    settings: Settings = Depends(get_settings),
    principal: Principal = Depends(require_roles("documents:write")),
) -> DocumentUploadUrlResponse:
    intent = await create_upload_intent(
        session,
        request,
        principal,
        settings,
        filename=payload.filename,
        mime_type=payload.mime_type,
        size_bytes=payload.size_bytes,
        sha256_hex=payload.sha256,
        language_hint=payload.language_hint,
    )
    await record_audit_event(
        session,
        principal=principal,
        action="upload_intent_created",
        resource_type="document",
        resource_id=intent.document_id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        metadata_json={"filename": payload.filename, "mime_type": payload.mime_type},
    )
    return DocumentUploadUrlResponse(**asdict(intent))


@router.put("/uploads/{upload_token}", name="receive_upload", response_model=UploadConfirmationResponse)
async def receive_upload(
    upload_token: str,
    request: Request,
    storage=Depends(get_storage),
    settings: Settings = Depends(get_settings),
) -> UploadConfirmationResponse:
    claims = decode_upload_intent_token(upload_token, settings)
    body = await request.body()
    expected_size = int(claims["size_bytes"])
    if len(body) != expected_size:
        raise APIError("VALIDATION_ERROR", "Uploaded content size does not match the reserved size.", 422)
    actual_hash = sha256(body).hexdigest()
    if actual_hash != str(claims["sha256"]):
        raise APIError("VALIDATION_ERROR", "Uploaded content hash does not match the reserved hash.", 422)
    await storage.save_bytes(str(claims["storage_key"]), body, str(claims["mime_type"]))
    return UploadConfirmationResponse(document_id=str(claims["document_id"]), status="stored")


@router.post(
    "/documents",
    response_model=DocumentCreateResponse,
    status_code=201,
)
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    language_hint: str | None = Form(default=None),
    session=Depends(get_session),
    settings: Settings = Depends(get_settings),
    storage=Depends(get_storage),
    principal: Principal = Depends(require_roles("documents:write", "jobs:run")),
) -> DocumentCreateResponse:
    data = await file.read()
    mime_type = _resolve_upload_mime(file)
    document = await save_direct_upload(
        session,
        storage,
        principal,
        settings,
        filename=file.filename or "document",
        mime_type=mime_type,
        data=data,
        language_hint=language_hint,
    )
    job = await create_or_resume_ocr_job(session, document, engine="pdfplumber")
    await session.commit()
    await record_audit_event(
        session,
        principal=principal,
        action="document_uploaded",
        resource_type="document",
        resource_id=document.id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        metadata_json={"filename": document.original_filename, "mime_type": document.mime_type},
    )
    return DocumentCreateResponse(document_id=document.id, job_id=job.id)


@router.post(
    "/documents/{document_id}/complete-upload",
    response_model=CompleteUploadResponse,
)
async def complete_upload(
    request: Request,
    document_id: str,
    session=Depends(get_session),
    storage=Depends(get_storage),
    principal: Principal = Depends(require_roles("documents:write", "jobs:run")),
) -> CompleteUploadResponse:
    document = await _load_document_or_404(session, principal, document_id)
    await finalize_upload(session, storage, document)
    job = await create_or_resume_ocr_job(session, document, engine="pdfplumber")
    await session.commit()
    if request is not None:
        await record_audit_event(
            session,
            principal=principal,
            action="upload_completed",
            resource_type="document",
            resource_id=document.id,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
    return CompleteUploadResponse(document_id=document.id, job_id=job.id, status=job.status)


@router.get("/documents", response_model=DocumentListResponse)
async def list_my_documents(
    session=Depends(get_session),
    principal: Principal = Depends(require_roles("documents:read")),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> DocumentListResponse:
    items, total = await list_documents(session, owner_sub=principal.sub, admin=principal.is_admin, limit=limit, offset=offset)
    return DocumentListResponse(limit=limit, offset=offset, total=total, items=[_document_response(item) for item in items])


@router.get("/documents/{document_id}", response_model=DocumentRead)
async def get_document_detail(
    document_id: str,
    session=Depends(get_session),
    principal: Principal = Depends(require_roles("documents:read")),
) -> DocumentRead:
    document = await _load_document_or_404(session, principal, document_id)
    return _document_response(document)


@router.get("/documents/{document_id}/download-url", response_model=DownloadUrlResponse)
async def get_document_download_url(
    request: Request,
    document_id: str,
    session=Depends(get_session),
    principal: Principal = Depends(require_roles("documents:read")),
) -> DownloadUrlResponse:
    document = await _load_document_or_404(session, principal, document_id)
    return DownloadUrlResponse(
        url=_build_download_url(request, document),
        expires_in_seconds=request.app.state.runtime.settings.download_url_ttl_seconds,
    )


@router.get("/documents/{document_id}/ocr-download-url", response_model=DownloadUrlResponse)
async def get_document_ocr_download_url(
    request: Request,
    document_id: str,
    session=Depends(get_session),
    principal: Principal = Depends(require_roles("documents:read")),
) -> DownloadUrlResponse:
    document = await _load_document_or_404(session, principal, document_id)
    return DownloadUrlResponse(
        url=_build_download_url(request, document, ocr=True),
        expires_in_seconds=request.app.state.runtime.settings.download_url_ttl_seconds,
    )


@router.get("/documents/{document_id}/download", name="download_document")
async def download_document(
    request: Request,
    document_id: str,
    session=Depends(get_session),
    storage=Depends(get_storage),
    principal: Principal = Depends(require_roles("documents:read")),
):
    document = await _load_document_or_404(session, principal, document_id)
    try:
        data = await storage.read_bytes(document.storage_original_key)
    except FileNotFoundError as exc:
        raise APIError("STORAGE_FILE_MISSING", "Original file is not available in local storage.", 404) from exc
    headers = {"Content-Disposition": f'attachment; filename="{quote(document.original_filename)}"'}
    await session.commit()
    await record_audit_event(
        session,
        principal=principal,
        action="document_downloaded",
        resource_type="document",
        resource_id=document.id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return StreamingResponse(io.BytesIO(data), media_type=document.mime_type, headers=headers)


@router.get("/documents/{document_id}/ocr-download", name="download_document_ocr")
async def download_document_ocr(
    request: Request,
    document_id: str,
    session=Depends(get_session),
    storage=Depends(get_storage),
    principal: Principal = Depends(require_roles("documents:read")),
):
    document = await _load_document_or_404(session, principal, document_id)
    key = document.storage_ocr_pdf_key or document.storage_original_key
    media_type = "application/pdf" if document.storage_ocr_pdf_key else document.mime_type
    filename = f"ocr-{quote(document.original_filename)}" if document.storage_ocr_pdf_key else quote(document.original_filename)
    try:
        data = await storage.read_bytes(key)
    except FileNotFoundError as exc:
        if key == document.storage_original_key:
            raise APIError("STORAGE_FILE_MISSING", "Original file is not available in local storage.", 404) from exc
        try:
            data = await storage.read_bytes(document.storage_original_key)
        except FileNotFoundError as original_exc:
            raise APIError("STORAGE_FILE_MISSING", "OCR file is not available in local storage.", 404) from original_exc
        media_type = document.mime_type
        filename = quote(document.original_filename)
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    await session.commit()
    await record_audit_event(
        session,
        principal=principal,
        action="ocr_document_downloaded",
        resource_type="document",
        resource_id=document.id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return StreamingResponse(io.BytesIO(data), media_type=media_type, headers=headers)


@router.get("/documents/{document_id}/text", response_model=DocumentTextResponse)
async def get_document_text(
    document_id: str,
    session=Depends(get_session),
    principal: Principal = Depends(require_roles("documents:read")),
) -> DocumentTextResponse:
    document = await _load_document_or_404(session, principal, document_id)
    pages = await get_document_pages(session, document.id)
    page_models = [
        DocumentPageRead(
            page_number=page.page_number,
            text_content=page.text_content,
            confidence=float(page.confidence) if page.confidence is not None else None,
            width=page.width,
            height=page.height,
        )
        for page in pages
    ]
    text = "\n".join(page.text_content or "" for page in page_models).strip()
    return DocumentTextResponse(
        document_id=document.id,
        original_filename=document.original_filename,
        page_count=document.page_count,
        text=text,
        pages=page_models,
    )


@router.delete("/documents/{document_id}", response_model=MessageResponse)
async def delete_document(
    request: Request,
    document_id: str,
    session=Depends(get_session),
    storage=Depends(get_storage),
    principal: Principal = Depends(require_roles("documents:delete")),
) -> MessageResponse:
    document = await _load_document_or_404(session, principal, document_id)
    if document.storage_original_key:
        await storage.delete(document.storage_original_key)
    if document.storage_ocr_pdf_key:
        await storage.delete(document.storage_ocr_pdf_key)
    await session.execute(delete(DocumentPage).where(DocumentPage.document_id == document.id))
    await session.execute(delete(DocumentSearch).where(DocumentSearch.document_id == document.id))
    await mark_document_deleted(session, document)
    await session.commit()
    await record_audit_event(
        session,
        principal=principal,
        action="document_deleted",
        resource_type="document",
        resource_id=document.id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return MessageResponse(message="Document deleted.")


@router.post("/documents/{document_id}/ocr", response_model=JobRead)
async def start_ocr(
    request: Request,
    document_id: str,
    session=Depends(get_session),
    principal: Principal = Depends(require_roles("jobs:run")),
) -> JobRead:
    document = await _load_document_or_404(session, principal, document_id)
    job = await create_or_resume_ocr_job(session, document, engine="pdfplumber")
    await session.commit()
    await record_audit_event(
        session,
        principal=principal,
        action="ocr_requested",
        resource_type="document",
        resource_id=document.id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return _job_response(job)
