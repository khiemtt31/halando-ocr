# UI/UX Design And Implementation Plan

This plan defines the best-fit UI direction for the current Document OCR API application. It is intentionally tied to the existing codebase: a local-first FastAPI app with a no-build browser UI served from `app/ui/test_ui.html` by `app/api/v1/endpoints/ui.py`.

## Goals

- Replace the current `/ui` entry point with `/home`.
- Split the current single long test page into user-focused app sections navigated through a top navbar.
- Add page navigation animations, tooltip guidance, loading states, and friendly empty/error states.
- Make the first app visit self-guided for users, not developers.
- Route strange browser URLs to a friendly not-found UI.
- Preserve API route behavior for `/api/v1/*` and keep API errors JSON-oriented.
- Keep the current no-build HTML/CSS/JavaScript approach unless a separate frontend toolchain is explicitly approved.

## Current Codebase Fit

The application currently has no JavaScript package manager, bundler, frontend framework, or static asset pipeline. The existing UI is a single HTML file:

| Area | Current Location | Notes |
| --- | --- | --- |
| UI HTML, CSS, JS | `app/ui/test_ui.html` | No-build browser UI with all behavior inline. |
| UI route | `app/api/v1/endpoints/ui.py` | Serves `/ui` as `HTMLResponse`. |
| Public route inclusion | `app/api/v1/router.py` | Public routes include health and UI. |
| App wiring | `app/main.py` | Public routes are included before `/api/v1`. |
| UI smoke test | `tests/test_ui.py` | Verifies `/ui`, title text, and `API_BASE`. |
| API docs | `docs/api.md` | Lists `/ui` as a public endpoint. |

The best UI plan is therefore a no-build single-page app served by FastAPI at `/home`, using browser-native routing, transitions, and accessibility patterns.

## Product Mental Model

Users need a guided path through document OCR:

1. Confirm the app is available.
2. Upload a PDF or image.
3. Wait for OCR processing.
4. Review extracted text.
5. Search documents.
6. Download or delete documents.
7. Adjust local demo identity only when they intentionally want to test another user.

The UI should make that sequence obvious without exposing implementation details first.

## Information Architecture

The top navbar should divide the current functions into clear user tasks:

| Navbar Item | Route | User Purpose | Current API/Code Mapping |
| --- | --- | --- | --- |
| Home | `/home` | Understand what to do next and see system status. | `/health`, `/ready`, current recommended flow. |
| Upload | `/home/upload` | Upload a PDF/image and create an OCR job. | `POST /api/v1/documents`. |
| Documents | `/home/documents` | Browse files, select documents, download, delete, or open text. | `GET /api/v1/documents`, document action endpoints. |
| Jobs | `/home/jobs` | Track OCR progress, poll jobs, retry, cancel, or start OCR. | `/api/v1/jobs/*`, `POST /api/v1/documents/{document_id}/ocr`. |
| Search | `/home/search` | Search all documents or one selected document. | `GET /api/v1/search`, `GET /api/v1/documents/{document_id}/search`. |
| Identity | `/home/identity` | Change local demo user and roles. | `x-demo-*` headers and `GET /api/v1/me`. |
| Admin | `/home/admin` | Inspect all local data when `admin:manage` is present. | `/api/v1/admin/documents`, `/jobs`, `/audit-events`. |
| Help | `/home/help` | Learn how to use the app in user language. | Existing docs summarized as user-facing guidance. |
| Not Found | `/home/not-found` | Recover from unknown browser routes. | New UI state. |

## Route Design

### Server Routes

Implement the browser UI route in `app/api/v1/endpoints/ui.py`:

| Route | Behavior |
| --- | --- |
| `GET /home` | Serve `app/ui/test_ui.html`. |
| `GET /home/{path:path}` | Serve `app/ui/test_ui.html`; JavaScript decides whether the path is a valid section or not-found. |
| `GET /ui` | Do not serve the UI. Return 404 unless a redirect is explicitly desired later. |

Avoid adding a broad catch-all route in `include_public_routes()` because public routes are included before the `/api/v1` router in `app/main.py`. A catch-all there could swallow unknown API paths.

### Strange URL Handling

For routes outside `/home`, use a 404 handler in `app/main.py` only if browser not-found UI is required globally.

Rules:

| Request | Response |
| --- | --- |
| `/api/v1/unknown` | Preserve API 404 behavior, preferably JSON. |
| `/home/unknown` | Serve UI shell and render not-found view. |
| `/strange-url` with HTML accept header | Serve a not-found UI if global browser fallback is implemented. |
| `/strange-url` without HTML accept header | Return JSON 404. |

FastAPI custom exception handling should distinguish API routes from browser routes. Do not replace existing `APIError` handling.

## Page Layout

### Global Shell

Use one persistent shell across all UI sections:

| Area | Content |
| --- | --- |
| Top navbar | Brand, primary nav, health/ready compact indicators, API docs link. |
| Main content | One active section at a time. |
| Guidance rail or banner | Contextual next step for the current section. |
| Toast/status region | Request success/failure feedback using `aria-live`. |
| API activity panel | Optional collapsible request log for advanced local inspection. |

### Home Page

The home page should answer: "What can I do now?"

Recommended content:

| Component | Details |
| --- | --- |
| Hero | "Turn PDFs and images into searchable text." |
| Status cards | API health, database readiness, current identity. |
| Guided steps | Upload, wait for OCR, search/read text, download or delete. |
| Primary action | "Upload a document" linking to `/home/upload`. |
| Secondary action | "View documents" linking to `/home/documents`. |

### Upload Page

The upload page should be direct and forgiving:

| Component | Details |
| --- | --- |
| File drop area | Accept PDF and image formats already supported by the current UI. |
| Language hint | Optional text field with visible guidance. |
| Upload action | Calls `POST /api/v1/documents`. |
| Result card | Shows document ID, job ID, and next action to track job. |
| Error state | Friendly message for size, type, role, or validation errors. |

### Documents Page

The documents page should be a library, not a raw table only:

| Component | Details |
| --- | --- |
| Toolbar | Refresh, status filter if added later, search shortcut. |
| Document cards or responsive table | File name, status, pages, created date, quick actions. |
| Selection behavior | Selecting a document fills shared document ID state for text/search/jobs. |
| Empty state | "No documents yet" with upload action. |
| Actions | Read text, start OCR, download original, download OCR, delete. |

### Jobs Page

The jobs page should explain OCR progress clearly:

| Component | Details |
| --- | --- |
| Job lookup | Existing job ID field. |
| Polling control | Start/stop polling with visible state. |
| Progress display | Status badge, progress value, attempt count, timestamps if available. |
| Actions | Start OCR for selected document, retry, cancel. |
| Guidance | Explain pending, running, completed, failed, cancelled in user terms. |

### Search Page

The search page should prioritize quick answers:

| Component | Details |
| --- | --- |
| Query input | Main search box. |
| Scope selector | All documents or selected document. |
| Results | File name, page number, snippet, action to open text. |
| Empty state | Explain that only processed documents are searchable. |

### Identity Page

Identity should be separated because most users should not need it every session:

| Component | Details |
| --- | --- |
| Identity fields | Subject, email, name, roles. |
| Save action | Persist to localStorage as the current UI already does. |
| Load `/me` action | Show resolved principal. |
| User warning | Explain that changing subject changes visible documents. |

### Admin Page

Admin should be shown only when the current roles include `admin:manage`:

| Component | Details |
| --- | --- |
| Admin documents | Calls `/api/v1/admin/documents`. |
| Admin jobs | Calls `/api/v1/admin/jobs`. |
| Audit events | Calls `/api/v1/admin/audit-events`. |
| Access state | If role is missing, explain that admin access is unavailable for this identity. |

### Help Page

Help should be written for users:

| Topic | Copy Direction |
| --- | --- |
| Uploads | "Choose a PDF or image from your computer." |
| OCR | "Processing may take a moment. Keep the worker running." |
| Search | "Search works after a document is processed." |
| Identity | "Changing identity changes which documents you can see." |
| Downloads | "OCR download returns the searchable PDF when available." |

Do not lead with developer commands. Keep Docker/API docs links secondary.

## Visual Design Direction

The current UI already uses a dark, technical visual language with blue/cyan accents. Preserve that direction, but make it more product-like:

| Token | Direction |
| --- | --- |
| Background | Dark radial gradient with subtle document-processing depth. |
| Surfaces | Layered cards with stronger hierarchy between primary and secondary panels. |
| Accent | Cyan/blue for primary actions, green for completed/healthy, amber for waiting, red for destructive/error. |
| Typography | System sans-serif, strong page titles, compact metadata using monospace only for IDs. |
| Layout | Desktop: wide shell with content cards. Mobile: single column with sticky top nav or horizontal nav scroll. |
| Density | Keep advanced API output collapsible so first-time users are not overwhelmed. |

## Animation Requirements

Animations are required, but they must not block accessibility.

Use these layers:

| Animation | Implementation |
| --- | --- |
| Page navigation | `document.startViewTransition()` when available. |
| Fallback page navigation | CSS opacity and translate transition. |
| Navbar active state | Sliding underline or pill movement. |
| Cards | Subtle enter transition on page render. |
| Status changes | Badge color and small scale/fade transition. |
| Loading | Skeleton or shimmer only for async loads. |
| Reduced motion | Disable non-essential transforms under `prefers-reduced-motion: reduce`. |

Use native View Transition API guidance from MDN: `Document.startViewTransition()` can animate between DOM states in a single-page app. Keep a safe fallback for unsupported browsers.

## Tooltip Requirements

Tooltips must be accessible and supplemental:

| Rule | Requirement |
| --- | --- |
| Association | Trigger uses `aria-describedby`; tooltip has `role="tooltip"`. |
| Trigger | Show on hover and keyboard focus. |
| Dismissal | Hide on blur, pointer out, and Escape. |
| Content | Text only; no buttons, links, or inputs inside tooltip. |
| Importance | Critical instructions must be visible in normal UI, not tooltip-only. |
| Touch | Do not rely on tooltip-only behavior for mobile users. |

Use tooltips for short help such as role meaning, language hint examples, polling explanation, and OCR download fallback.

## State Management Plan

Keep simple browser state in inline JavaScript:

| State | Storage |
| --- | --- |
| Current route | `window.location.pathname` plus History API. |
| Identity fields | Existing `localStorage` keys. |
| Selected document ID | In-memory state plus related input fields. |
| Selected job ID | In-memory state plus related input fields. |
| API request log | In-memory visible panel. |
| Last successful upload | In-memory result card. |

Do not add a client-side state library.

## JavaScript Structure

The current inline script can stay in one file but should be organized into sections:

| Section | Responsibilities |
| --- | --- |
| Constants | `API_BASE`, routes, selectors, storage keys. |
| DOM helpers | `$`, `escapeHtml`, output writers, live status updates. |
| Router | route table, navigation click handling, History API, not-found fallback. |
| Transitions | `navigateWithTransition()`, reduced-motion checks. |
| Tooltips | setup, Escape handling, focus/hover behavior. |
| API client | `authHeaders()`, `request()`, `downloadFile()`, API logging. |
| Identity | load/save identity, load `/me`. |
| Documents | upload, list, render, select, delete, download, text. |
| Jobs | get, poll, start, retry, cancel. |
| Search | global and scoped search. |
| Admin | admin list rendering. |
| Boot | load identity, bind events, route initial path, check health. |

Keep functions small and domain-named. Do not introduce framework-like abstractions.

## Accessibility Requirements

| Area | Requirement |
| --- | --- |
| Landmarks | Use `header`, `nav`, `main`, `section`, and clear headings. |
| Navbar | Use links or buttons with `aria-current="page"` on active item. |
| Focus | Move focus to the new page heading after route navigation. |
| Status messages | Use an `aria-live="polite"` region for request outcomes. |
| Forms | Every input must have a visible label. |
| Errors | Error text should be next to the affected action or form. |
| Tables | Keep column headings and readable mobile layout. |
| Color | Do not rely on color alone for status. Keep text labels. |
| Motion | Honor `prefers-reduced-motion`. |

## User Guidance Requirements

Guidance must speak to the user, not the developer.

Examples:

| Avoid | Prefer |
| --- | --- |
| "POST to `/api/v1/documents`." | "Choose a file and upload it to start OCR." |
| "Poll the job endpoint." | "Track progress until OCR is complete." |
| "Set `x-demo-sub`." | "Use another identity when you want a separate document library." |
| "Worker container must run." | "Processing only completes while OCR processing is running locally." |

Developer links to `/docs` and project docs can remain secondary.

## Implementation Phases

### Phase 1: Routing And Entry Point

Files:

| File | Change |
| --- | --- |
| `app/api/v1/endpoints/ui.py` | Replace `/ui` with `/home` and `/home/{path:path}`. |
| `tests/test_ui.py` | Update route expectations from `/ui` to `/home`. |
| `docs/*` and `README.md` | Replace public user-facing `/ui` references with `/home`. |

Acceptance:

- `GET /home` returns the UI shell.
- `GET /home/upload` returns the UI shell.
- `GET /ui` no longer serves the UI.

### Phase 2: UI Shell And Navbar

Files:

| File | Change |
| --- | --- |
| `app/ui/test_ui.html` | Add top navbar, route sections, home page, and not-found view. |

Acceptance:

- All current functions remain available.
- Navbar navigation updates browser history.
- Refreshing `/home/documents` opens the correct section.
- Unknown `/home/*` paths render the not-found section.

### Phase 3: Animations And Tooltips

Files:

| File | Change |
| --- | --- |
| `app/ui/test_ui.html` | Add transition CSS/JS, accessible tooltip behavior, reduced-motion support. |

Acceptance:

- Navigation is animated in browsers that support View Transition API.
- Fallback transition works without View Transition API.
- Tooltips work by hover and focus and dismiss with Escape.
- Reduced-motion users do not receive transform-heavy animation.

### Phase 4: Guidance And Responsive Polish

Files:

| File | Change |
| --- | --- |
| `app/ui/test_ui.html` | Rewrite visible guidance, add empty states, improve mobile layout. |

Acceptance:

- A new user can follow the flow from home to upload to OCR to search without reading docs.
- Mobile layout remains usable without horizontal page overflow except inside tables where intentional.
- Advanced API log is secondary or collapsible.

### Phase 5: Browser Not Found Handling

Files:

| File | Change |
| --- | --- |
| `app/main.py` | Add careful browser 404 handling only if global strange URL fallback is required. |

Acceptance:

- Strange browser URLs show not-found UI.
- Unknown `/api/v1/*` routes do not get swallowed by the UI shell.

## Test Plan

Update or add tests:

| Test | Expected |
| --- | --- |
| `GET /home` | `200`, contains app shell title and `const API_BASE = "/api/v1"`. |
| `GET /home/upload` | `200`, contains app shell. |
| `GET /home/not-a-section` | `200`, app shell can render not-found state. |
| `GET /ui` | Does not return the old UI. |
| `GET /api/v1/not-a-route` | API route behavior remains JSON/error-oriented. |
| Existing document flow smoke test | Still passes. |

Manual checks:

| Check | Expected |
| --- | --- |
| Desktop navigation | Top nav is clear and animated. |
| Mobile navigation | Nav remains reachable and readable. |
| Keyboard only | User can navigate, upload controls are focusable, tooltips appear on focus. |
| Reduced motion | Page transitions are minimized. |
| Missing roles | UI shows clear permission errors from API responses. |
| Empty document library | User sees upload guidance. |

Run:

```bash
.venv/bin/ruff check app tests
.venv/bin/python -m compileall app tests
.venv/bin/pytest
```

## Documentation Updates After Implementation

Update these `/ui` references after the route is changed:

| File | Current Topic |
| --- | --- |
| `README.md` | Quick start and structure. |
| `docs/api.md` | Public endpoint table. |
| `docs/docker.md` | Local usage instructions. |
| `docs/architecture.md` | UI ownership. |
| `docs/local-development.md` | Local app URLs. |
| `docs/structure-checklist.md` | Structure note. |
| `docs/application-flow.md` | Browser client flow. |
| `docs/test-ui.md` | Rename or rewrite as home UI documentation. |
| `fastapi_document_ocr_api_plan.md` | Legacy planning reference if still maintained. |

## Skill Files

Supporting implementation guidance lives in:

| Skill File | Purpose |
| --- | --- |
| `.agent/skills/no-build-fastapi-ui.md` | How to edit this UI without adding a frontend build system. |
| `.agent/skills/accessible-guided-ui.md` | User guidance, accessibility, tooltip, and keyboard rules. |
| `.agent/skills/native-view-transitions.md` | Page transition implementation rules and fallbacks. |

## External References Used

| Reference | Applied Decision |
| --- | --- |
| MDN View Transition API | Use `document.startViewTransition()` for same-document SPA route transitions with fallback. |
| MDN ARIA tooltip role | Use `aria-describedby`, `role="tooltip"`, focus/hover behavior, Escape dismissal, and no interactive tooltip content. |
| FastAPI error handling docs | Use route or exception handling carefully so browser not-found UI does not break API errors. |

## Non-Goals

- Do not add React, Vite, npm, Tailwind, or another frontend stack unless explicitly approved.
- Do not add production authentication flows.
- Do not remove existing local demo auth behavior.
- Do not bypass API role or ownership checks in the UI.
- Do not make tooltips the only place where critical instructions appear.
