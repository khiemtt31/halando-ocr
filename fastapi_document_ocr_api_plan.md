# FastAPI Document/OCR API Local Docker Plan

## Goal

Maintain a local Docker-only Document/OCR API. The project should be easy to start, reset, inspect, and test on a developer machine.

The product flow remains:

1. User uploads a PDF/image.
2. API stores the original file locally.
3. API creates document metadata and an OCR job.
4. Worker extracts/OCRs text.
5. User can read, search, download, or delete their own documents.

## Supported Runtime

Only this runtime is supported:

```text
Docker Compose
  api     -> FastAPI/Uvicorn on localhost:8000
  worker  -> OCR worker polling SQLite
  data    -> ./data bind-mounted to /app/data
```

There is no supported public hosting, remote storage, external database, or external identity-provider mode.

## Local Services

- `api`: serves FastAPI routes and OpenAPI docs.
- `worker`: processes pending OCR jobs.
- `./data/dococr.db`: SQLite database.
- `./data/storage/`: original files and OCR output PDFs.

## Auth

Use local demo auth only.

- User identity comes from `x-demo-*` request headers.
- Defaults come from `.env`.
- Roles are still enforced by API dependencies.
- No login/password flow or external identity provider is maintained.

Useful roles:

```text
documents:read,documents:write,documents:delete,jobs:read,jobs:run,admin:manage
```

## Storage

Use local filesystem storage only.

Storage keys follow this layout under `/app/data/storage`:

```text
tenants/{tenant_id}/users/{local_sub}/documents/{document_id}/original/{filename}
tenants/{tenant_id}/users/{local_sub}/documents/{document_id}/ocr/output.pdf
```

The local storage backend resolves keys under the configured storage root and rejects keys that try to escape it.

## Database

Use SQLite only for local development and demos.

- Schema is auto-created on startup.
- Delete `./data` to reset all local state.
- No migrations are required while this remains a local-only source.

## OCR

- Use `pdfplumber` first for machine-readable PDFs.
- Use OCRmyPDF/Tesseract fallback when the worker container has native OCR tools available.
- Mark jobs failed when no usable text is produced.

## API Scope

- Health/readiness endpoints
- Local no-build test UI at `/ui`
- `/api/v1/me`
- Document upload/direct-upload/download/text/delete/list/detail
- OCR job list/detail/retry/cancel/start
- Search current user's documents
- Admin list endpoints for local inspection

## Local Commands

Start:

```bash
docker compose up --build
```

Create `.env` only when local overrides are needed.

Open the browser test UI at `http://localhost:8000/ui`.

Stop:

```bash
docker compose down
```

Reset:

```bash
docker compose down
rm -rf data
```

Verify outside Docker:

```bash
.venv/bin/ruff check app tests
.venv/bin/python -m compileall app tests
.venv/bin/pytest
```

Primary handoff docs live in `README.md` and `docs/`.

## Out Of Scope

- Public hosting
- Remote object storage
- External database services
- External identity providers
- Distributed queues
- Production hardening
