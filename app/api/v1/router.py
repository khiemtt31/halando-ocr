from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.endpoints.admin import router as admin_router
from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.documents import router as documents_router
from app.api.v1.endpoints.health import router as health_router
from app.api.v1.endpoints.jobs import router as jobs_router
from app.api.v1.endpoints.me import router as me_router
from app.api.v1.endpoints.search import router as search_router
from app.api.v1.endpoints.ui import router as ui_router

router = APIRouter(prefix="/api/v1")
router.include_router(auth_router)
router.include_router(me_router)
router.include_router(documents_router)
router.include_router(jobs_router)
router.include_router(search_router)
router.include_router(admin_router)


def include_public_routes(app_router: APIRouter) -> None:
    app_router.include_router(health_router)
    app_router.include_router(ui_router)
