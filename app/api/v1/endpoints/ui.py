from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["ui"])

TEST_UI_PATH = Path(__file__).resolve().parents[3] / "ui" / "test_ui.html"


@router.get("/ui", response_class=HTMLResponse, include_in_schema=False)
def test_ui() -> HTMLResponse:
    return HTMLResponse(TEST_UI_PATH.read_text(encoding="utf-8"))
