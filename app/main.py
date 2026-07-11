from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from uuid import uuid4

import uvicorn
from fastapi import APIRouter, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import include_public_routes
from app.api.v1.router import router as api_v1_router
from app.core.config import Settings, get_settings
from app.core.errors import APIError, error_response
from app.core.logging import configure_logging
from app.core.runtime import build_runtime, close_runtime, init_database, seed_database

logger = logging.getLogger(__name__)


def create_app(settings: Settings | None = None) -> FastAPI:
    runtime_settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        configure_logging()
        runtime = build_runtime(runtime_settings)
        app.state.runtime = runtime
        if runtime_settings.auto_create_schema:
            await init_database(runtime)
            await seed_database(runtime)
        try:
            yield
        finally:
            await close_runtime(runtime)

    app = FastAPI(
        title="Document OCR API",
        description="FastAPI backend for authenticated document upload, OCR jobs, extracted text, and search.",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=runtime_settings.cors_allow_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    public_router = APIRouter()
    include_public_routes(public_router)
    app.include_router(public_router)
    app.include_router(api_v1_router)

    @app.exception_handler(APIError)
    async def api_error_handler(request: Request, exc: APIError) -> JSONResponse:
        request_id = request.headers.get("x-request-id") or f"req_{uuid4().hex}"
        return JSONResponse(
            status_code=exc.status_code,
            content=error_response(request_id, exc.code, exc.message),
            headers={"x-request-id": request_id},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        request_id = request.headers.get("x-request-id") or f"req_{uuid4().hex}"
        return JSONResponse(
            status_code=422,
            content=error_response(request_id, "VALIDATION_ERROR", str(exc)),
            headers={"x-request-id": request_id},
        )

    @app.exception_handler(Exception)
    async def unexpected_error_handler(request: Request, exc: Exception) -> JSONResponse:
        request_id = request.headers.get("x-request-id") or f"req_{uuid4().hex}"
        logger.exception("Unhandled request error %s", request_id)
        return JSONResponse(
            status_code=500,
            content=error_response(request_id, "INTERNAL_ERROR", "Internal server error."),
            headers={"x-request-id": request_id},
        )

    return app


app = create_app()


def main() -> None:
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    main()
