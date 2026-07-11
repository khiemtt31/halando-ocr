# Structure And Checklist

## Implemented

- Project metadata and dependency groups in `pyproject.toml`.
- Docker Compose stack with separate API and worker images.
- FastAPI app factory in `app/main.py`.
- Health and readiness endpoints.
- Local no-build browser test UI served at `/ui`.
- Local demo auth through `x-demo-*` headers.
- Role-based dependencies with `require_roles(...)`.
- SQLAlchemy models for users, documents, jobs, pages, search, and audit events.
- SQLite local database with automatic schema creation.
- Local filesystem storage backend with path escape protection.
- Multipart upload endpoint.
- Local direct-upload intent endpoint.
- Direct-upload receiver with token, size, and SHA-256 validation.
- Document ownership enforcement for normal users.
- OCR job lifecycle endpoints.
- Worker loop and one-shot worker mode.
- PDF text extraction with `pdfplumber`.
- OCRmyPDF/Tesseract hooks in the Docker worker image.
- Extracted text endpoint.
- OCR download fallback to the original file when OCR output is unavailable.
- Search endpoints scoped by user.
- Admin list endpoints for local inspection.
- Audit event recording for important actions.
- End-to-end smoke test for upload, OCR, text, search, and delete.
- Storage unit tests for local save, read, exists, delete, and path safety.
- Junior-friendly docs for architecture, flow, Docker, API, and development guidelines.

## Not Maintained In This Source

- Public hosting guides.
- Cloud-specific runtime scaffolding.
- Remote object storage backends.
- External database runtime paths.
- External identity provider paths.
- Distributed queue infrastructure.
- Database migrations.

## Files To Review First

- `README.md`: project purpose, quick start, structure, and reading path.
- `docs/application-flow.md`: step-by-step behavior.
- `docs/docker.md`: local Docker commands and troubleshooting.
- `docs/test-ui.md`: browser test UI workflow.
- `docs/architecture.md`: runtime components and code layers.
- `docs/development-guidelines.md`: rules for safe code changes.
- `docker-compose.yml`: local service shape and bind mounts.
- `.env.example`: local defaults.
- `app/api/v1/endpoints/`: route behavior and role requirements.
- `app/core/security.py`: local demo user behavior.
- `app/models/`: database shape before keeping local data long term.
- `app/services/storage.py`: local file behavior.
- `app/workers/ocr_pipeline.py`: OCR fallback thresholds.

## Before Marking Work Done

- Run `ruff check app tests`.
- Run `python -m compileall app tests`.
- Run `pytest`.
- Update docs for any changed behavior.
- Reset `data/` when model changes make old local SQLite data stale.
