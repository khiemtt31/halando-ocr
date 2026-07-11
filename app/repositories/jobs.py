from __future__ import annotations

from uuid import uuid4

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.time import utcnow
from app.models.document import Document
from app.models.ocr_job import OCRJob


async def get_job(session: AsyncSession, job_id: str, *, owner_sub: str | None = None, admin: bool = False) -> OCRJob | None:
    stmt = select(OCRJob).join(Document, Document.id == OCRJob.document_id).where(OCRJob.id == job_id)
    if owner_sub and not admin:
        stmt = stmt.where(Document.owner_sub == owner_sub)
    return (await session.scalars(stmt)).first()


def _apply_visibility(stmt: Select, *, owner_sub: str | None = None, admin: bool = False) -> Select:
    if owner_sub and not admin:
        stmt = stmt.where(Document.owner_sub == owner_sub)
    return stmt


async def list_jobs(
    session: AsyncSession,
    *,
    owner_sub: str | None = None,
    admin: bool = False,
    status: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[OCRJob], int]:
    stmt = select(OCRJob).join(Document, Document.id == OCRJob.document_id)
    stmt = _apply_visibility(stmt, owner_sub=owner_sub, admin=admin)
    if status:
        stmt = stmt.where(OCRJob.status == status)
    stmt = stmt.order_by(OCRJob.created_at.desc()).offset(offset).limit(limit)
    items = list((await session.scalars(stmt)).all())

    count_stmt = select(func.count()).select_from(OCRJob).join(Document, Document.id == OCRJob.document_id)
    count_stmt = _apply_visibility(count_stmt, owner_sub=owner_sub, admin=admin)
    if status:
        count_stmt = count_stmt.where(OCRJob.status == status)
    total = int((await session.execute(count_stmt)).scalar_one())
    return items, total


async def get_active_job_for_document(session: AsyncSession, document_id: str) -> OCRJob | None:
    stmt = select(OCRJob).where(OCRJob.document_id == document_id, OCRJob.status.in_(["pending", "running"]))
    return (await session.scalars(stmt)).first()


async def ensure_job(session: AsyncSession, document: Document, *, engine: str = "pdfplumber") -> OCRJob:
    active = await get_active_job_for_document(session, document.id)
    if active is not None:
        return active
    job = OCRJob(
        id=str(uuid4()),
        document_id=document.id,
        status="pending",
        engine=engine,
        progress=0,
        attempt_count=0,
        max_attempts=3,
        created_at=utcnow(),
        updated_at=utcnow(),
    )
    document.status = "processing"
    document.updated_at = utcnow()
    session.add(job)
    await session.flush()
    return job


async def claim_next_pending_job(session: AsyncSession) -> tuple[OCRJob, Document] | None:
    stmt = (
        select(OCRJob, Document)
        .join(Document, Document.id == OCRJob.document_id)
        .where(OCRJob.status == "pending", Document.status != "deleted")
        .order_by(OCRJob.created_at.asc())
        .limit(1)
    )
    row = (await session.execute(stmt)).first()
    if row is None:
        return None
    job, document = row
    job.status = "running"
    job.progress = max(job.progress, 10)
    job.started_at = utcnow()
    job.updated_at = utcnow()
    document.status = "processing"
    document.updated_at = utcnow()
    await session.flush()
    return job, document


async def mark_job_running(session: AsyncSession, job: OCRJob) -> OCRJob:
    job.status = "running"
    job.progress = max(job.progress, 10)
    job.started_at = job.started_at or utcnow()
    job.updated_at = utcnow()
    await session.flush()
    return job


async def mark_job_completed(session: AsyncSession, job: OCRJob, document: Document, *, page_count: int, ocr_pdf_key: str | None) -> OCRJob:
    job.status = "completed"
    job.progress = 100
    job.error_code = None
    job.error_message = None
    job.finished_at = utcnow()
    job.updated_at = utcnow()
    document.status = "processed"
    document.page_count = page_count
    document.storage_ocr_pdf_key = ocr_pdf_key or document.storage_ocr_pdf_key
    document.updated_at = utcnow()
    await session.flush()
    return job


async def mark_job_failed(session: AsyncSession, job: OCRJob, document: Document, *, code: str, message: str) -> OCRJob:
    job.status = "failed"
    job.error_code = code
    job.error_message = message
    job.finished_at = utcnow()
    job.updated_at = utcnow()
    document.status = "failed"
    document.updated_at = utcnow()
    await session.flush()
    return job


async def retry_job(session: AsyncSession, job: OCRJob, document: Document) -> OCRJob:
    if job.status not in {"failed", "cancelled"}:
        return job
    if job.attempt_count >= job.max_attempts:
        return job
    job.status = "pending"
    job.progress = 0
    job.attempt_count += 1
    job.error_code = None
    job.error_message = None
    job.started_at = None
    job.finished_at = None
    job.updated_at = utcnow()
    document.status = "processing"
    document.updated_at = utcnow()
    await session.flush()
    return job


async def cancel_job(session: AsyncSession, job: OCRJob, document: Document) -> OCRJob:
    if job.status in {"completed", "cancelled"}:
        return job
    job.status = "cancelled"
    job.finished_at = utcnow()
    job.updated_at = utcnow()
    if document.status == "processing":
        document.status = "uploaded"
        document.updated_at = utcnow()
    await session.flush()
    return job
