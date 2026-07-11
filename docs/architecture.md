# Architecture

## Scope

This project is a local Docker-only Document OCR API. It uses local containers, local SQLite, local filesystem storage, and local demo auth.

The goal is not to be a production platform. The goal is to provide a clear backend that can upload documents, run OCR locally, search extracted text, and demonstrate clean FastAPI structure.

## Runtime Components

```text
Client
  -> api container
       -> FastAPI routes
       -> local demo auth
       -> SQLite metadata, jobs, pages, search, audit
       -> local filesystem storage

worker container
  -> SQLite pending jobs
  -> local filesystem original files
  -> PDF text extraction or OCR
  -> SQLite page/search rows
  -> local filesystem OCR output PDF when available
```

## Code Layers

- `app/main.py`: creates the FastAPI app, runtime, middleware, routers, and exception handlers.
- `app/api/deps.py`: exposes dependencies for settings, sessions, storage, principals, and role checks.
- `app/api/v1/endpoints/`: owns HTTP routes and keeps request/response behavior close to FastAPI.
- `app/services/`: owns business rules such as upload validation, storage keys, audit, and search orchestration.
- `app/repositories/`: owns SQLAlchemy query and persistence functions.
- `app/models/`: owns SQLAlchemy database table definitions.
- `app/schemas/`: owns Pydantic request and response models.
- `app/ui/`: owns the local no-build browser test UI served at `/ui`.
- `app/workers/`: owns job polling and OCR extraction.
- `app/core/`: owns configuration, runtime setup, security, errors, logging, and time helpers.

## Startup

1. Docker starts the `api` container.
2. `create_app` builds the runtime from settings.
3. The runtime creates the async SQLAlchemy engine, session factory, auth provider, and local storage backend.
4. If `AUTO_CREATE_SCHEMA=true`, SQLAlchemy creates missing tables.
5. Docker waits for the API healthcheck.
6. Docker starts the `worker` container after the API is healthy.
7. The worker builds its own runtime and polls pending OCR jobs.

## Data Flow

```text
Upload request
  -> validate auth, roles, size, MIME type
  -> write original file to data/storage
  -> insert document row
  -> insert OCR job row
  -> record audit event

Worker loop
  -> claim pending job
  -> read original file from data/storage
  -> extract text or OCR
  -> replace document_pages and document_search rows
  -> save OCR output PDF when produced
  -> mark job/document completed or failed

Read/search/download
  -> validate auth and roles
  -> enforce owner_sub unless admin
  -> return metadata, text, search hits, or file stream
```

## Database

SQLite lives at `data/dococr.db` on the host and `/app/data/dococr.db` in containers.

Important tables:

- `users`: local demo user records.
- `documents`: document metadata, ownership, storage keys, and processing status.
- `ocr_jobs`: job status, progress, attempts, and errors.
- `document_pages`: extracted text per page.
- `document_search`: searchable lower-cased page content.
- `audit_events`: local audit trail for important actions.

There are no migrations today. When models change, reset local data with `docker compose down` and `rm -rf data`.

## Storage

Local files live under `data/storage` on the host and `/app/data/storage` in containers.

Storage keys follow this shape:

```text
tenants/{tenant_id}/users/{owner_sub}/documents/{document_id}/original/{filename}
tenants/{tenant_id}/users/{owner_sub}/documents/{document_id}/ocr/output.pdf
```

The storage backend resolves paths and rejects keys that escape the configured storage root.

## Auth And Ownership

The app uses local demo auth only.

Request headers can override the local user:

```text
x-demo-sub: user-1
x-demo-email: user@example.com
x-demo-name: Demo User
x-demo-roles: documents:read,documents:write,documents:delete,jobs:read,jobs:run,admin:manage
```

Every document stores `owner_sub`. Normal users can only access their own documents. Admin access requires `admin:manage` and is meant for local inspection.

## OCR Strategy

- Machine-readable PDFs are extracted with `pdfplumber` first.
- PDFs with too little text try OCRmyPDF when the worker image has native OCR tooling available.
- Images try Tesseract through the worker image.
- Jobs fail when no usable text is produced.

## Operational Boundaries

- The API and worker communicate through SQLite, not a queue service.
- The download URL endpoints return local role-protected API routes, not public signed object-storage links.
- The worker is single-process and local-focused.
- `data/` is disposable and ignored by git.
