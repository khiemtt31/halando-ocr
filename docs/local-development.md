# Local Development

Use this as the short runbook after you understand the main README and `docs/docker.md`.

## Requirements

- Docker Desktop or a compatible Docker Compose runtime.
- Optional Python `3.14.x` for running lint and tests outside containers.

## Start The Stack

```bash
docker compose up --build
```

The stack contains these local services:

- `api`: FastAPI app on `http://localhost:8000`.
- `worker`: OCR worker polling the shared SQLite database.
- `./data:/app/data`: bind mount shared by API and worker.

Create `.env` only when you want to override defaults from `.env.example`.

## URLs

- Test UI: `http://localhost:8000/ui`
- API docs: `http://localhost:8000/docs`
- Health: `http://localhost:8000/health`
- Ready: `http://localhost:8000/ready`

## Local Data

Default local data is written under `data/`:

- SQLite DB: `data/dococr.db`
- Stored files: `data/storage/`

Delete `data/` to reset local state:

```bash
docker compose down
rm -rf data
```

## Demo Auth

No external identity provider is used. The API reads the current local user from request headers or `.env` defaults.

Useful headers:

```text
x-demo-sub: user-1
x-demo-email: user@example.com
x-demo-name: Demo User
x-demo-roles: documents:read,documents:write,documents:delete,jobs:read,jobs:run,admin:manage
```

## Run Checks Outside Docker

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -e '.[dev]'
.venv/bin/ruff check app tests
.venv/bin/python -m compileall app tests
.venv/bin/pytest
```

## API Client Notes

The repository includes minimal Bruno collection metadata in `infra/bruno/doc-ocr-api`. The local environment sets `base_url` to `http://localhost:8000`.

Swagger UI at `http://localhost:8000/docs` is still the fastest way to try the API.
