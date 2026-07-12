from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, HTMLResponse

router = APIRouter(tags=["ui"])

UI_DIR = Path(__file__).resolve().parents[3] / "ui"
UI_PATH = UI_DIR / "home_ui.html"


@router.get("/ui/{asset_path:path}", include_in_schema=False)
def ui_asset(asset_path: str) -> FileResponse:
    asset = (UI_DIR / asset_path).resolve()
    try:
        asset.relative_to(UI_DIR)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="UI asset not found") from exc
    if not asset.is_file():
        raise HTTPException(status_code=404, detail="UI asset not found")
    return FileResponse(asset)


@router.get("/home", response_class=HTMLResponse, include_in_schema=False)
@router.get("/home/{path:path}", response_class=HTMLResponse, include_in_schema=False)
def home_ui(path: str = "") -> HTMLResponse:
    return HTMLResponse(UI_PATH.read_text(encoding="utf-8"))
