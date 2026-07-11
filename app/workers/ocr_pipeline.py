from __future__ import annotations

import logging

from app.core.config import Settings
from app.models.document import Document
from app.services.storage import StorageBackend
from app.workers.engines.pdf_text import extract_pdf_text

logger = logging.getLogger(__name__)


class OCRPipelineError(Exception):
    pass


async def extract_document_pages(
    *,
    storage: StorageBackend,
    settings: Settings,
    document: Document,
) -> tuple[list[dict[str, object]], bytes | None]:
    data = await storage.read_bytes(document.storage_original_key)
    language = document.language_hint or settings.ocr_default_language

    if document.source_type == "pdf":
        pages = extract_pdf_text(data, settings.ocr_max_pages)
        useful_chars = sum(len(str(page.get("text_content") or "").strip()) for page in pages)
        if useful_chars >= 50:
            return pages, data
        try:
            from app.workers.engines.ocrmypdf_engine import run_ocrmypdf

            ocr_pdf = await run_ocrmypdf(data, language, settings.ocr_timeout_seconds)
            pages = extract_pdf_text(ocr_pdf, settings.ocr_max_pages)
            return pages, ocr_pdf
        except Exception as exc:
            logger.warning("OCRmyPDF failed or is unavailable; returning direct extraction result", exc_info=exc)
            if pages:
                return pages, None
            raise OCRPipelineError(f"PDF OCR failed: {exc}") from exc

    if document.source_type == "image":
        try:
            from app.workers.engines.tesseract_engine import extract_image_text

            return extract_image_text(data, language), None
        except Exception as exc:
            raise OCRPipelineError(f"Image OCR failed: {exc}") from exc

    raise OCRPipelineError(f"Unsupported source type: {document.source_type}")
