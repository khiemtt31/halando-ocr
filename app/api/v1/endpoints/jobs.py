from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import select

from app.api.deps import get_session, require_roles
from app.core.errors import APIError
from app.core.security import Principal
from app.models.document import Document
from app.repositories.jobs import cancel_job, get_job, list_jobs, retry_job
from app.schemas.job import JobListResponse, JobRead
from app.services.audit import record_audit_event

router = APIRouter(tags=["jobs"])


async def _load_job_or_404(session, principal: Principal, job_id: str):
    job = await get_job(session, job_id, owner_sub=principal.sub, admin=principal.is_admin)
    if job is None:
        raise APIError("OCR_JOB_NOT_FOUND", "OCR job not found or access denied.", 404)
    return job


async def _load_job_document(session, job) -> Document:
    document = (await session.scalars(select(Document).where(Document.id == job.document_id))).first()
    if document is None:
        raise APIError("DOCUMENT_NOT_FOUND", "Document not found or access denied.", 404)
    return document


@router.get("/jobs/{job_id}", response_model=JobRead)
async def get_ocr_job(
    job_id: str,
    session=Depends(get_session),
    principal: Principal = Depends(require_roles("jobs:read")),
) -> JobRead:
    job = await _load_job_or_404(session, principal, job_id)
    return JobRead.model_validate(job)


@router.get("/jobs", response_model=JobListResponse)
async def list_ocr_jobs(
    session=Depends(get_session),
    principal: Principal = Depends(require_roles("jobs:read")),
    status: str | None = Query(default=None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> JobListResponse:
    items, total = await list_jobs(
        session,
        owner_sub=principal.sub,
        admin=principal.is_admin,
        status=status,
        limit=limit,
        offset=offset,
    )
    return JobListResponse(limit=limit, offset=offset, total=total, items=[JobRead.model_validate(item) for item in items])


@router.post("/jobs/{job_id}/retry", response_model=JobRead)
async def retry_ocr_job(
    request: Request,
    job_id: str,
    session=Depends(get_session),
    principal: Principal = Depends(require_roles("jobs:run")),
) -> JobRead:
    job = await _load_job_or_404(session, principal, job_id)
    document = await _load_job_document(session, job)
    if job.status not in {"failed", "cancelled"}:
        raise APIError("OCR_JOB_ALREADY_RUNNING", "Only failed or cancelled jobs can be retried.", 409)
    if job.attempt_count >= job.max_attempts:
        raise APIError("OCR_FAILED", "Job has reached the maximum retry count.", 409)
    await retry_job(session, job, document)
    await session.commit()
    await record_audit_event(
        session,
        principal=principal,
        action="ocr_job_retried",
        resource_type="ocr_job",
        resource_id=job.id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return JobRead.model_validate(job)


@router.post("/jobs/{job_id}/cancel", response_model=JobRead)
async def cancel_ocr_job(
    request: Request,
    job_id: str,
    session=Depends(get_session),
    principal: Principal = Depends(require_roles("jobs:run")),
) -> JobRead:
    job = await _load_job_or_404(session, principal, job_id)
    document = await _load_job_document(session, job)
    await cancel_job(session, job, document)
    await session.commit()
    await record_audit_event(
        session,
        principal=principal,
        action="ocr_job_cancelled",
        resource_type="ocr_job",
        resource_id=job.id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return JobRead.model_validate(job)
