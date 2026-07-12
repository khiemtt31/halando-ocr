# Document OCR API

Local Docker-only FastAPI application for uploading PDF/image documents, extracting searchable text, and downloading the original or OCR-generated output files.

This repository is intentionally small and local-first so it is easy to learn, run, reset, and change safely.

## Current Scope

- `api`: FastAPI application exposed at `http://localhost:8000`.
- `worker`: background OCR worker that polls pending jobs.
- `data/dococr.db`: local SQLite database created automatically.
- `data/storage/`: local filesystem storage for uploaded and generated files.
- Local demo auth only through `x-demo-*` headers and `.env` defaults.

The maintained runtime is Docker Compose on a developer machine. Public hosting, external identity providers, remote object storage, and production database runtimes are not maintained in this source.

## First Reading Path

Read these in order if you are new to the project:

1. `README.md`: what the application is and how to start it.
2. `docs/application-flow.md`: step-by-step request, worker, search, and delete flow.
3. `docs/docker.md`: Docker commands, reset workflow, logs, and troubleshooting.
4. `docs/architecture.md`: code layers, runtime components, storage, database, and auth.
5. `docs/home-ui.md`: browser UI workflow.
6. `docs/api.md`: endpoint guide and role requirements.
7. `docs/development-guidelines.md`: rules for adding features without making the codebase hard to maintain.

## Quick Start

Requirement:

- Docker Desktop or another Docker Compose-compatible runtime.

Start the stack:

```bash
docker compose up --build
```

After the first build, normal edits under `app/` hot reload inside Docker. Use this day to day:

```bash
docker compose up
```

Rebuild only after changing dependencies, Dockerfiles, or OCR system packages.

Create `.env` only when you need local overrides:

```bash
cp .env.example .env
```

Open the app:

- Home UI: `http://localhost:8000/home`
- API docs: `http://localhost:8000/docs`
- Health: `http://localhost:8000/health`
- Ready: `http://localhost:8000/ready`

Stop the stack:

```bash
docker compose down
```

Reset all local data:

```bash
docker compose down
rm -rf data
```

## Main Flow

1. A user uploads a PDF/image with `POST /api/v1/documents` or creates a direct-upload intent.
2. The API validates size, MIME type, local roles, and ownership.
3. The API stores the original file under `data/storage/` and creates a document row.
4. The API creates a pending OCR job for the document.
5. The `worker` container claims the pending job from SQLite.
6. The worker extracts PDF text with `pdfplumber` or falls back to OCRmyPDF/Tesseract when needed.
7. The worker stores extracted page text and search rows in SQLite.
8. The user reads text, searches documents, downloads files, retries jobs, or deletes documents through the API.

## Project Structure

```text
app/
  api/                  FastAPI dependencies, routers, and endpoint handlers
  core/                 Settings, security, runtime setup, logging, and shared errors
  db/                   SQLAlchemy base and async session/engine setup
  models/               SQLAlchemy tables for documents, jobs, pages, users, search, audit
  repositories/         Database query and persistence functions
  schemas/              Pydantic request and response models
  services/             Business rules for documents, audit, search, and storage
  ui/                   No-build browser Home UI served at /home
  workers/              OCR worker loop and OCR/extraction pipeline
docs/                   Human-readable architecture, flow, Docker, API, and dev docs
infra/bruno/            Minimal Bruno API collection metadata for local requests
```

The code is organized so endpoint files stay focused on HTTP concerns, services hold business rules, repositories hold database access, and workers handle background OCR processing.

## Local Auth

The app uses local demo auth only. There is no login screen.

By default, requests run as the demo user configured in `.env.example`. You can simulate another user or role set with request headers:

```text
x-demo-sub: user-1
x-demo-email: user@example.com
x-demo-name: Demo User
x-demo-roles: documents:read,documents:write,documents:delete,jobs:read,jobs:run,admin:manage
```

The API still enforces roles, so missing roles return `403`.

## Useful Docker Commands

Run in the foreground with hot reload:

```bash
docker compose up
```

Run in the background with hot reload:

```bash
docker compose up -d
```

Build or rebuild images:

```bash
docker compose up --build
```

Follow logs:

```bash
docker compose logs -f api worker
```

Process one pending job manually:

```bash
docker compose run --rm worker python -m app.workers.ocr_worker --once
```

Rebuild from scratch:

```bash
docker compose down
docker compose build --no-cache
docker compose up
```

See the full Docker runbook in `docs/docker.md`.

## Local Files

Runtime data lives in `data/`:

```text
data/
  dococr.db
  storage/
    tenants/
      default/
        users/
          demo-user/
```

`data/` is ignored by git and can be deleted whenever you want a clean local state.

## Configuration

Docker Compose loads `.env.example` first and optional `.env` overrides second.

Important local settings:

- `DATABASE_URL=sqlite+aiosqlite:////app/data/dococr.db`
- `LOCAL_STORAGE_ROOT=/app/data/storage`
- `DEMO_DEFAULT_ROLES=documents:read,documents:write,documents:delete,jobs:read,jobs:run`
- `MAX_UPLOAD_SIZE_MB=25`
- `OCR_DEFAULT_LANGUAGE=eng`
- `OCR_MAX_PAGES=50`

## Development Checks

Run these outside Docker when changing code:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -e '.[dev]'
.venv/bin/ruff check app
.venv/bin/python -m compileall app
```

Use Docker smoke checks for upload, worker processing, extracted text, search, and delete flows.

## Troubleshooting

If the API is not ready, check API logs:

```bash
docker compose logs -f api
```

If jobs stay pending, check worker logs:

```bash
docker compose logs -f worker
```

If model changes make local data stale, reset `data/`:

```bash
docker compose down
rm -rf data
docker compose up --build
```
