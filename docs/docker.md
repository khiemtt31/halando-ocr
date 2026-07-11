# Docker Guide

This project is designed to run locally with Docker Compose. Docker is the primary development runtime because the worker needs native OCR tools that are easier to keep inside the worker image.

## Files To Know

- `docker-compose.yml`: defines the `keycloak`, `api`, and `worker` services, mounts `./app:/app/app` for hot reload, and mounts `./data:/app/data` for runtime data.
- `Dockerfile.api`: installs the FastAPI application dependencies; Compose starts Uvicorn with reload enabled.
- `Dockerfile.worker`: installs OCR system packages and OCR Python dependencies; Compose starts the worker through `watchfiles`.
- `infra/keycloak/halando-realm.json`: imports the local Keycloak realm, client, roles, and seeded demo account.
- `.env.example`: default local configuration loaded by Docker Compose.
- `.env`: optional local-only overrides ignored by git.

## Services

- `keycloak`: runs the local Keycloak server on `http://localhost:8080` and imports the `halando` realm.
- `api`: serves HTTP requests on `http://localhost:8000`.
- `worker`: waits for pending OCR jobs and processes them.
- `app`: bind-mounted source folder watched by both containers.
- `data`: bind-mounted local folder shared by both containers.

## Local Keycloak

The local realm is imported from `infra/keycloak/halando-realm.json` every time the Keycloak container is recreated. It defines the public OIDC client `halando-api`, the API roles, and this seeded account:

```text
username: demo
password: demo123!
```

The API validates bearer tokens from Keycloak. `KEYCLOAK_SERVER_URL` is the container-internal URL used by the API to fetch signing keys, while `KEYCLOAK_PUBLIC_SERVER_URL` is the browser-facing URL used by `/ui`.

If you run the API outside Docker but keep Keycloak in Compose, override `KEYCLOAK_SERVER_URL=http://localhost:8080` because `http://keycloak:8080` only resolves inside the Compose network.

## Start From Clean Repository

1. Install Docker Desktop or a compatible Docker Compose runtime.
2. Open a terminal in the repository root.
3. Run `docker compose up --build`.
4. Wait until the API healthcheck passes and the worker starts.
5. Open `http://localhost:8000/ui` for the browser UI or `http://localhost:8000/docs` for Swagger UI.
6. Sign in through Keycloak with `demo` / `demo123!`.
7. Upload a PDF/image from the UI, Swagger UI, or an API client.
8. For later Python edits under `app/`, keep Compose running; the API and worker reload automatically.

## Day-To-Day Commands

Run foreground with hot reload:

```bash
docker compose up
```

Run background with hot reload:

```bash
docker compose up -d
```

Build or rebuild images:

```bash
docker compose up --build
```

You only need to rebuild after changing `pyproject.toml`, a Dockerfile, OCR system packages, or other image-level dependencies. Regular changes under `app/` are applied by the running containers.

Stop containers while keeping local data:

```bash
docker compose down
```

Follow Keycloak, API, and worker logs:

```bash
docker compose logs -f keycloak api worker
```

Follow only worker logs:

```bash
docker compose logs -f worker
```

Run one worker pass manually:

```bash
docker compose run --rm worker python -m app.workers.ocr_worker --once
```

Rebuild without cache:

```bash
docker compose build --no-cache
```

## Reset Local State

Use this when schema changes, test data is confusing, or the app behaves differently from the docs.

```bash
docker compose down
rm -rf data
docker compose up --build
```

This deletes the local SQLite database and every uploaded/generated file.

## Environment Overrides

Docker Compose loads `.env.example` and then optional `.env`.

Create `.env` only when you want to override defaults:

```bash
cp .env.example .env
```

Common overrides:

- `MAX_UPLOAD_SIZE_MB`: change local upload size limit.
- `OCR_DEFAULT_LANGUAGE`: default OCR language, for example `eng` or `vie`.
- `WORKER_POLL_INTERVAL_SECONDS`: worker sleep time when no jobs are pending.
- `AUTH_PROVIDER`: use `keycloak` for local Docker or `local` for header-based development/test auth.
- `KEYCLOAK_SERVER_URL`: Keycloak URL reachable from the API container, normally `http://keycloak:8080`.
- `KEYCLOAK_PUBLIC_SERVER_URL`: Keycloak URL reachable from your browser, normally `http://localhost:8080`.
- `DEMO_DEFAULT_ROLES`: default role set when `AUTH_PROVIDER=local`.
- `CORS_ALLOW_ORIGINS`: allowed browser origins.

## Health Checks

API health endpoint:

```bash
curl http://localhost:8000/health
```

API readiness endpoint:

```bash
curl http://localhost:8000/ready
```

`/health` confirms the app is running. `/ready` confirms the app can query the database.

## OCR Notes

The API image does not install native OCR tools. The worker image installs Tesseract, OCRmyPDF dependencies, Ghostscript, QPDF, Poppler, and Unpaper.

If OCR fails for images or scanned PDFs, check the worker logs first because failures usually come from OCR tooling, language packs, malformed files, or timeouts.

## Troubleshooting

If `http://localhost:8000/docs` does not load, run `docker compose logs -f api`.

If uploaded jobs stay pending, run `docker compose logs -f worker`.

If the worker says the database or storage path is missing, verify `docker-compose.yml` still mounts `./data:/app/data` for both services.

If a model changed and old data causes errors, reset with `docker compose down`, `rm -rf data`, and `docker compose up --build`.

If Docker seems to use old dependencies, run `docker compose build --no-cache`.

If port `8000` is already used, stop the other process or change the host port mapping in `docker-compose.yml`.
