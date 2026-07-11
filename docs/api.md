# API Guide

Base URL for versioned endpoints: `/api/v1`.

Interactive docs: `http://localhost:8000/docs`.

## Auth Model

The app uses local demo auth. There is no login endpoint.

Default identity and roles come from `.env.example` or `.env`. Requests can override them with headers:

```text
x-demo-sub: user-1
x-demo-email: user@example.com
x-demo-name: Demo User
x-demo-roles: documents:read,documents:write,documents:delete,jobs:read,jobs:run,admin:manage
```

Missing roles return `403`. Missing or inaccessible documents return `404` so users cannot distinguish between absent and unauthorized documents.

## Public Endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/health` | Confirms the API process is alive. |
| `GET` | `/ready` | Confirms the API can query the database. |
| `GET` | `/ui` | Local no-build browser UI for testing the API. |
| `GET` | `/docs` | FastAPI Swagger UI. |

## User Endpoint

| Method | Path | Role | Purpose |
| --- | --- | --- | --- |
| `GET` | `/api/v1/me` | Any local user | Returns the resolved local demo principal. |

## Document Endpoints

| Method | Path | Role | Purpose |
| --- | --- | --- | --- |
| `POST` | `/api/v1/documents` | `documents:write`, `jobs:run` | Multipart upload that stores a file and creates an OCR job. |
| `POST` | `/api/v1/documents/upload-url` | `documents:write` | Creates a local direct-upload intent and signed upload URL. |
| `PUT` | `/api/v1/uploads/{upload_token}` | Signed token | Receives raw bytes for a direct-upload intent. |
| `POST` | `/api/v1/documents/{document_id}/complete-upload` | `documents:write`, `jobs:run` | Verifies direct-upload storage and creates/resumes an OCR job. |
| `GET` | `/api/v1/documents` | `documents:read` | Lists the current user's non-deleted documents. |
| `GET` | `/api/v1/documents/{document_id}` | `documents:read` | Returns document metadata if owned by the current user. |
| `GET` | `/api/v1/documents/{document_id}/text` | `documents:read` | Returns combined extracted text and page-level text. |
| `GET` | `/api/v1/documents/{document_id}/download-url` | `documents:read` | Returns the local route for downloading the original file. |
| `GET` | `/api/v1/documents/{document_id}/ocr-download-url` | `documents:read` | Returns the local route for downloading the OCR output file. |
| `GET` | `/api/v1/documents/{document_id}/download` | `documents:read` | Streams the original file. |
| `GET` | `/api/v1/documents/{document_id}/ocr-download` | `documents:read` | Streams OCR output if available, otherwise the original file with its original media type. |
| `DELETE` | `/api/v1/documents/{document_id}` | `documents:delete` | Deletes local files, page/search rows, and marks the document deleted. |

Download URL responses are local API routes, not public signed object-storage URLs.

## Job Endpoints

| Method | Path | Role | Purpose |
| --- | --- | --- | --- |
| `POST` | `/api/v1/documents/{document_id}/ocr` | `jobs:run` | Creates or resumes an OCR job for a document. |
| `GET` | `/api/v1/jobs/{job_id}` | `jobs:read` | Reads one OCR job if visible to the current user. |
| `GET` | `/api/v1/jobs?status=pending` | `jobs:read` | Lists visible OCR jobs, optionally filtered by status. |
| `POST` | `/api/v1/jobs/{job_id}/retry` | `jobs:run` | Retries a failed or cancelled job if attempts remain. |
| `POST` | `/api/v1/jobs/{job_id}/cancel` | `jobs:run` | Cancels a job unless it is already completed or cancelled. |

## Search Endpoints

| Method | Path | Role | Purpose |
| --- | --- | --- | --- |
| `GET` | `/api/v1/search?q=invoice` | `documents:read` | Searches processed documents owned by the current user. |
| `GET` | `/api/v1/documents/{document_id}/search?q=total` | `documents:read` | Searches one processed document owned by the current user. |

Search uses lower-cased text stored in SQLite. It is suitable for local demos, not advanced production search.

## Admin Endpoints

All admin endpoints require `admin:manage`.

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/api/v1/admin/documents` | Lists documents across local users, including deleted documents. |
| `GET` | `/api/v1/admin/jobs` | Lists jobs across local users. |
| `GET` | `/api/v1/admin/audit-events` | Lists audit events. |

## Error Shape

Errors use a stable envelope:

```json
{
  "error": {
    "code": "DOCUMENT_NOT_FOUND",
    "message": "Document not found or access denied.",
    "request_id": "req_..."
  }
}
```

The response also includes the same request ID in the `x-request-id` header.

## Pagination

List endpoints use `limit` and `offset` query parameters.

Defaults:

- `limit=20`
- `offset=0`
- maximum `limit=100`
