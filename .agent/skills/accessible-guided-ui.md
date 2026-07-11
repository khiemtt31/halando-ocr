# Accessible Guided UI Skill

Use this skill when writing UI copy, navigation, forms, tooltips, status messages, empty states, or error states for this repository's browser UI.

## Product Goal

The UI should guide a user through document OCR without requiring API knowledge:

1. Check app readiness.
2. Upload a PDF or image.
3. Track OCR progress.
4. Read extracted text.
5. Search processed documents.
6. Download or delete documents.

## User-Facing Copy Rules

- Write for users first, developers second.
- Prefer task language over API language.
- Keep important instructions visible.
- Put developer/API details behind secondary links, collapsible panels, or logs.
- Explain local demo identity only where users manage identity.

Use this translation style:

| Avoid | Prefer |
| --- | --- |
| "POST `/api/v1/documents`." | "Upload a document to start OCR." |
| "Poll job endpoint." | "Track progress until processing finishes." |
| "Set `x-demo-sub`." | "Switch identity to view a different local document library." |
| "403 from role check." | "This identity does not have permission for that action." |

## Accessibility Rules

- Use semantic landmarks: `header`, `nav`, `main`, `section`, and headings.
- Use real buttons for actions and links for navigation.
- Mark the active navigation item with `aria-current="page"`.
- Move focus to the active page heading after route navigation.
- Every form control needs a visible label.
- Use `aria-live="polite"` for request success and failure feedback.
- Keep status labels textual; do not rely on color alone.
- Preserve keyboard-only operation for all primary actions.
- Honor `prefers-reduced-motion: reduce`.

## Tooltip Rules

Use tooltips only for supplemental context.

| Rule | Requirement |
| --- | --- |
| Trigger | The owner element uses `aria-describedby`. |
| Tooltip | The tooltip element uses `role="tooltip"`. |
| Opening | Show on pointer hover and keyboard focus. |
| Closing | Hide on blur, pointer out, and Escape. |
| Content | Text only; no links, buttons, inputs, or menus. |
| Critical guidance | Must be visible outside the tooltip. |

Good tooltip subjects:

| Control | Tooltip Intent |
| --- | --- |
| Language hint | Give examples like `eng` or `vie`. |
| Polling | Explain that it refreshes job progress automatically. |
| OCR download | Explain fallback to original file if OCR PDF is not available. |
| Roles | Explain that roles control which actions are allowed. |

## Empty And Error States

Every async area should have these states:

| State | Requirement |
| --- | --- |
| Empty | Explain why there is no content and offer a next action. |
| Loading | Show that work is happening without blocking navigation. |
| Success | Confirm what changed and suggest the next step. |
| Error | Show a concise message based on API error content. |

Examples:

| Area | Empty State |
| --- | --- |
| Documents | "No documents yet. Upload a PDF or image to start OCR." |
| Search | "No results. Search works after a document has finished processing." |
| Jobs | "No job selected. Upload a document or choose a document to start OCR." |

## Review Checklist

- Can a new user follow the main flow without reading developer docs?
- Can a keyboard-only user navigate and trigger actions?
- Are all instructions needed for success visible, not tooltip-only?
- Are API logs secondary instead of the primary UI?
- Are errors recoverable with a next action?
