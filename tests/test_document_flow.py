from __future__ import annotations

import io

import pytest
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient
from reportlab.pdfgen import canvas

from app.core.config import Settings
from app.main import create_app
from app.workers.ocr_worker import process_one_pending_job


def make_pdf(text: str) -> bytes:
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer)
    pdf.drawString(72, 720, text)
    pdf.save()
    return buffer.getvalue()


@pytest.mark.asyncio
async def test_upload_process_search_and_delete_document(tmp_path) -> None:
    settings = Settings(
        auth_provider="local",
        database_url=f"sqlite+aiosqlite:///{tmp_path / 'dococr.db'}",
        local_storage_root=tmp_path / "storage",
        demo_default_roles="documents:read,documents:write,documents:delete,jobs:read,jobs:run,admin:manage",
        auto_create_schema=True,
    )
    app = create_app(settings)
    pdf_bytes = make_pdf("Invoice ABC-123 total 100 dollars")

    async with (
        LifespanManager(app),
        AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client,
    ):
        health = await client.get("/health")
        assert health.status_code == 200

        upload = await client.post(
            "/api/v1/documents",
            files={"file": ("invoice.pdf", pdf_bytes, "application/pdf")},
        )
        assert upload.status_code == 201, upload.text
        document_id = upload.json()["document_id"]
        job_id = upload.json()["job_id"]

        processed = await process_one_pending_job(app.state.runtime)
        assert processed is True

        job = await client.get(f"/api/v1/jobs/{job_id}")
        assert job.status_code == 200, job.text
        assert job.json()["status"] == "completed"

        text = await client.get(f"/api/v1/documents/{document_id}/text")
        assert text.status_code == 200, text.text
        assert "Invoice ABC-123" in text.json()["text"]

        search = await client.get("/api/v1/search", params={"q": "ABC-123"})
        assert search.status_code == 200, search.text
        assert search.json()["total"] == 1

        detail = await client.get(f"/api/v1/documents/{document_id}")
        assert detail.status_code == 200, detail.text
        ocr_key = detail.json()["storage_ocr_pdf_key"]
        await app.state.runtime.storage.delete(ocr_key)

        ocr_download = await client.get(f"/api/v1/documents/{document_id}/ocr-download")
        assert ocr_download.status_code == 200, ocr_download.text
        assert ocr_download.content == pdf_bytes

        delete = await client.delete(f"/api/v1/documents/{document_id}")
        assert delete.status_code == 200, delete.text

        missing = await client.get(f"/api/v1/documents/{document_id}")
        assert missing.status_code == 404
