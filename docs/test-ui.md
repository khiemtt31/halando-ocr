# Test UI

The app serves a local no-build test UI at `http://localhost:8000/ui`.

## Purpose

Use the test UI when you want to manually exercise the API without Swagger request forms, curl commands, or a separate frontend app.

It is meant for local development only.

## What It Can Test

- Health and readiness checks.
- Local demo identity headers.
- `GET /api/v1/me`.
- Multipart document uploads.
- OCR job lookup, polling, retry, cancel, and start.
- Document list and document selection.
- Extracted text retrieval.
- Search across documents or inside one document.
- Original and OCR file downloads with the configured demo headers.
- Document deletion.

## How To Use It

1. Start Docker with `docker compose up --build`.
2. Open `http://localhost:8000/ui`.
3. Keep the default identity unless you want to test another local user.
4. Upload a PDF or image.
5. Poll the returned job ID until the worker marks it `completed` or `failed`.
6. Use the document actions to read text, search, download, or delete.

## Important Notes

- The worker container still needs to be running for OCR jobs to complete.
- If you change `x-demo-sub`, you are acting as a different local user and will not see the previous user's documents.
- Downloads use `fetch` so the page can send the same `x-demo-*` headers as other API requests.
- The page has no build step and lives in `app/ui/test_ui.html`.
- The FastAPI route that serves it lives in `app/api/v1/endpoints/ui.py`.
