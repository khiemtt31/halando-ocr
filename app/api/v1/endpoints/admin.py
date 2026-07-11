from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_session, require_roles
from app.repositories.audit import list_audit_events
from app.repositories.documents import list_documents
from app.repositories.jobs import list_jobs
from app.schemas.audit import AuditEventListResponse, AuditEventRead
from app.schemas.document import DocumentListResponse, DocumentRead
from app.schemas.job import JobListResponse, JobRead

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/documents", response_model=DocumentListResponse)
async def admin_list_documents(
    session=Depends(get_session),
    _principal=Depends(require_roles("admin:manage")),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> DocumentListResponse:
    items, total = await list_documents(session, admin=True, include_deleted=True, limit=limit, offset=offset)
    return DocumentListResponse(limit=limit, offset=offset, total=total, items=[DocumentRead.model_validate(item) for item in items])


@router.get("/jobs", response_model=JobListResponse)
async def admin_list_jobs(
    session=Depends(get_session),
    _principal=Depends(require_roles("admin:manage")),
    status: str | None = Query(default=None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> JobListResponse:
    items, total = await list_jobs(session, admin=True, status=status, limit=limit, offset=offset)
    return JobListResponse(limit=limit, offset=offset, total=total, items=[JobRead.model_validate(item) for item in items])


@router.get("/audit-events", response_model=AuditEventListResponse)
async def admin_list_audit_events(
    session=Depends(get_session),
    _principal=Depends(require_roles("admin:manage")),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> AuditEventListResponse:
    items, total = await list_audit_events(session, limit=limit, offset=offset)
    return AuditEventListResponse(limit=limit, offset=offset, total=total, items=[AuditEventRead.model_validate(item) for item in items])
