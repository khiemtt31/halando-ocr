from __future__ import annotations

import argparse
import asyncio
import logging

from sqlalchemy import select

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.core.runtime import build_runtime, close_runtime, init_database, seed_database
from app.models.document import Document
from app.repositories.jobs import claim_next_pending_job, mark_job_completed, mark_job_failed
from app.repositories.pages import replace_document_pages
from app.workers.ocr_pipeline import extract_document_pages

logger = logging.getLogger(__name__)


async def process_one_pending_job(runtime) -> bool:
    async with runtime.sessionmaker() as session:
        claimed = await claim_next_pending_job(session)
        if claimed is None:
            await session.commit()
            return False
        job, document = claimed
        await session.commit()

    async with runtime.sessionmaker() as session:
        document = (await session.scalars(select(Document).where(Document.id == document.id))).first()
        if document is None:
            return True
        job = await session.get(type(job), job.id)
        if job is None:
            return True
        try:
            pages, ocr_pdf = await extract_document_pages(storage=runtime.storage, settings=runtime.settings, document=document)
            if not pages or not any(str(page.get("text_content") or "").strip() for page in pages):
                raise ValueError("OCR produced no text")
            if ocr_pdf and document.storage_ocr_pdf_key:
                await runtime.storage.save_bytes(document.storage_ocr_pdf_key, ocr_pdf, "application/pdf")
            await replace_document_pages(session, document_id=document.id, owner_sub=document.owner_sub, pages=pages)
            await mark_job_completed(
                session,
                job,
                document,
                page_count=len(pages),
                ocr_pdf_key=document.storage_ocr_pdf_key if ocr_pdf else None,
            )
            await session.commit()
            logger.info("Processed OCR job %s for document %s", job.id, document.id)
        except Exception as exc:
            await mark_job_failed(session, job, document, code="OCR_FAILED", message=str(exc))
            await session.commit()
            logger.exception("Failed OCR job %s", job.id)
    return True


async def run_worker(*, once: bool = False) -> None:
    configure_logging()
    runtime = build_runtime(get_settings())
    try:
        if runtime.settings.auto_create_schema:
            await init_database(runtime)
            await seed_database(runtime)
        while True:
            processed = await process_one_pending_job(runtime)
            if once:
                return
            if not processed:
                await asyncio.sleep(runtime.settings.worker_poll_interval_seconds)
    finally:
        await close_runtime(runtime)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the document OCR worker")
    parser.add_argument("--once", action="store_true", help="Process at most one pending job then exit")
    args = parser.parse_args()
    asyncio.run(run_worker(once=args.once))


if __name__ == "__main__":
    main()
