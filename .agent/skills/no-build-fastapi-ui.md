# No-Build FastAPI UI Skill

Use this skill when implementing or reviewing UI changes for this repository's browser interface.

## Context

This repository is a local-first FastAPI Document OCR app. The browser UI is intentionally no-build:

| Area | Location |
| --- | --- |
| UI source | `app/ui/test_ui.html` |
| UI route | `app/api/v1/endpoints/ui.py` |
| Router inclusion | `app/api/v1/router.py` |
| App setup | `app/main.py` |
| UI tests | `tests/test_ui.py` |

There is no frontend package manager, bundler, framework, or static asset pipeline.

## Rules

- Keep UI changes in `app/ui/test_ui.html` unless the server route must change.
- Do not add React, Vite, npm, Tailwind, or a build system without explicit approval.
- Keep API calls pointed at `const API_BASE = "/api/v1"`.
- Use the existing local demo auth headers: `x-demo-sub`, `x-demo-email`, `x-demo-name`, and `x-demo-roles`.
- Preserve role and ownership enforcement by calling the API normally.
- Keep browser state simple: URL path, in-memory state, and existing `localStorage` identity values.
- Prefer small, direct functions over framework-like abstractions.
- Update tests and docs when public routes change.

## Route Guidance

For the planned UI redesign:

| Route | Behavior |
| --- | --- |
| `/home` | Serve the UI shell. |
| `/home/{path:path}` | Serve the same UI shell and let browser JavaScript render the section. |
| `/ui` | Do not serve the old UI unless a redirect is explicitly requested. |

Avoid broad public catch-all routes because public routes are included before `/api/v1`. A public catch-all can accidentally capture API requests.

## Implementation Workflow

1. Inspect `app/ui/test_ui.html` before editing.
2. Map each UI action to an existing API endpoint in `docs/api.md` or `app/api/v1/endpoints/*`.
3. Change the minimal server route code needed in `app/api/v1/endpoints/ui.py`.
4. Keep route-specific UI behavior in browser JavaScript.
5. Update `tests/test_ui.py` for route expectations.
6. Update docs that mention the old UI route.

## Verification

Run the relevant checks:

```bash
.venv/bin/ruff check app tests
.venv/bin/python -m compileall app tests
.venv/bin/pytest tests/test_ui.py
```

Run the full test suite before considering larger UI route changes complete:

```bash
.venv/bin/pytest
```
