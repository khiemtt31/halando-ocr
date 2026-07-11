# Application Flow

This document explains how the application behaves from request to database to worker to response.

## Mental Model

The API owns request validation, auth, metadata, and user-facing responses. The worker owns background OCR processing. SQLite is the shared coordination point between them. Local storage contains the original uploaded files and optional OCR output PDFs.

The local test UI at `/ui` is a browser client for the same API flow. It does not bypass auth, role checks, ownership checks, or the worker.

## Data Created By The App

- `documents`: one row per uploaded document.
- `ocr_jobs`: one row per OCR attempt or reusable active job.
- `document_pages`: extracted text per page.
- `document_search`: lower-cased searchable page content.
- `audit_events`: local inspection records for important user actions.
- `data/storage/.../original/...`: original uploaded file bytes.
- `data/storage/.../ocr/output.pdf`: OCR output PDF when the pipeline produces one.

## Roles Used In The Flow

- `documents:write`: create upload intents, upload documents, and complete direct uploads.
- `documents:read`: list, read, search, and download documents.
- `documents:delete`: delete documents.
- `jobs:run`: create, retry, and cancel OCR jobs.
- `jobs:read`: read and list OCR jobs.
- `admin:manage`: inspect all documents, jobs, and audit events locally.

## Flow 1: Multipart Upload

1. Client sends `POST /api/v1/documents` with multipart field `file` and optional `language_hint`.
2. FastAPI resolves the local demo user from `x-demo-*` headers or `.env.example` defaults.
3. The route requires `documents:write` and `jobs:run`.
4. The API reads the uploaded bytes and resolves the MIME type from the request or filename.
5. `save_direct_upload` validates size and source type, calculates SHA-256, creates the storage key, writes bytes to local storage, and creates the document row.
6. `create_or_resume_ocr_job` creates a pending OCR job unless the document already has an active one.
7. The API commits the document and job, records an audit event, and returns `document_id` plus `job_id`.
8. The worker eventually processes the pending job.

## Flow 2: Direct Upload Intent

1. Client sends `POST /api/v1/documents/upload-url` with filename, MIME type, byte size, SHA-256, and optional language hint.
2. The route requires `documents:write`.
3. `create_upload_intent` validates metadata, creates a document row, signs a local upload token, and returns an upload URL.
4. Client sends raw bytes to `PUT /api/v1/uploads/{upload_token}`.
5. The upload receiver validates token kind, expected size, and SHA-256 before saving bytes to local storage.
6. Client sends `POST /api/v1/documents/{document_id}/complete-upload`.
7. The route requires `documents:write` and `jobs:run`, verifies the file exists, and creates or resumes the OCR job.
8. The API records an audit event and returns the job status.

## Flow 3: Worker Processing

1. The `worker` container starts after the API healthcheck passes.
2. The worker opens its own runtime with the same SQLite database and storage root.
3. `claim_next_pending_job` selects the oldest pending job for a non-deleted document.
4. The job status becomes `running`, progress moves to at least `10`, and the document status becomes `processing`.
5. `extract_document_pages` reads the original file from local storage.
6. For PDFs, the pipeline first uses `pdfplumber` to extract text.
7. If extracted PDF text is too small, the pipeline tries OCRmyPDF and then extracts text from the OCR PDF.
8. For images, the pipeline tries Tesseract.
9. If no usable text is produced, the job is marked `failed` and the document is marked `failed`.
10. If text is produced, page rows and search rows are replaced, optional OCR PDF bytes are saved, the job becomes `completed`, and the document becomes `processed`.

## Flow 4: Read, Search, And Download

1. Client lists documents with `GET /api/v1/documents`.
2. Client reads metadata with `GET /api/v1/documents/{document_id}`.
3. Client reads extracted text with `GET /api/v1/documents/{document_id}/text`.
4. Client searches all own processed documents with `GET /api/v1/search?q=invoice`.
5. Client searches inside one processed document with `GET /api/v1/documents/{document_id}/search?q=total`.
6. Client asks for a local download route with `GET /api/v1/documents/{document_id}/download-url` or `GET /api/v1/documents/{document_id}/ocr-download-url`.
7. Client downloads through the returned local route while still using local demo auth.

Download URL responses include `expires_in_seconds` for client behavior, but the local download routes themselves are role-protected API routes rather than signed public links.

The OCR download route streams the OCR output PDF when it exists and falls back to the original file when the OCR output file is unavailable.

## Flow 5: Delete

1. Client sends `DELETE /api/v1/documents/{document_id}`.
2. The route requires `documents:delete`.
3. The API verifies ownership unless the user has admin access.
4. The API deletes original and OCR output files from local storage if they exist.
5. The API deletes extracted page and search rows.
6. The API marks the document row as `deleted` instead of hard-deleting it.
7. Normal document queries hide deleted rows.
8. Admin document listing can include deleted rows for local inspection.

## Status Lifecycles

Document statuses:

```text
uploaded -> processing -> processed
uploaded -> processing -> failed
processed -> deleted
failed -> uploaded -> processing
```

Job statuses:

```text
pending -> running -> completed
pending -> running -> failed
failed -> pending
pending/running/failed -> cancelled
```

## Ownership Rule

Every document has an `owner_sub`. Normal requests only see rows where `documents.owner_sub` matches the current local demo principal. Admin requests require `admin:manage` and are intended only for local inspection.
