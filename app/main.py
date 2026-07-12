from __future__ import annotations

import logging
import socket
from contextlib import asynccontextmanager
from ipaddress import ip_address
from uuid import uuid4

import uvicorn
from fastapi import APIRouter, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.v1.endpoints.ui import UI_PATH
from app.api.v1.router import include_public_routes
from app.api.v1.router import router as api_v1_router
from app.core.config import Settings, get_settings
from app.core.errors import APIError, error_response
from app.core.logging import configure_logging
from app.core.runtime import build_runtime, close_runtime, init_database, seed_database

logger = logging.getLogger(__name__)

ACCESS_LOG_PATHS = (("UI", "/home"), ("API docs", "/docs"), ("Health", "/health"))


def _format_url_host(host: str) -> str:
    return f"[{host}]" if ":" in host else host


def _access_url(settings: Settings, host: str, path: str) -> str:
    return f"http://{_format_url_host(host)}:{settings.server_port}{path}"


def _network_interface_ips() -> list[str]:
    ips: set[str] = set()

    def add_ip(value: str) -> None:
        try:
            parsed = ip_address(value.split("%", 1)[0])
        except ValueError:
            return
        if parsed.is_loopback or parsed.is_link_local or parsed.is_multicast or parsed.is_unspecified:
            return
        ips.add(str(parsed))

    for hostname in {socket.gethostname(), socket.getfqdn()}:
        try:
            for address_info in socket.getaddrinfo(hostname, None, type=socket.SOCK_STREAM):
                add_ip(address_info[4][0])
        except OSError:
            continue

    for family, target in (
        (socket.AF_INET, ("8.8.8.8", 80)),
        (socket.AF_INET6, ("2001:4860:4860::8888", 80, 0, 0)),
    ):
        try:
            with socket.socket(family, socket.SOCK_DGRAM) as outbound_socket:
                outbound_socket.connect(target)
                add_ip(outbound_socket.getsockname()[0])
        except OSError:
            continue

    return sorted(ips, key=lambda value: (ip_address(value).version, int(ip_address(value))))


def _log_urls_for_host(label: str, host: str, settings: Settings) -> None:
    urls = " | ".join(f"{name}: {_access_url(settings, host, path)}" for name, path in ACCESS_LOG_PATHS)
    logger.info("  %s %s", label, urls)


def _log_startup_access_urls(settings: Settings) -> None:
    private_ips: list[str] = []
    public_ips: list[str] = []
    for address in _network_interface_ips():
        parsed = ip_address(address)
        if parsed.is_private:
            private_ips.append(address)
        elif parsed.is_global:
            public_ips.append(address)

    logger.info("Application access URLs:")
    _log_urls_for_host("Localhost:", "localhost", settings)
    for address in private_ips:
        _log_urls_for_host(f"Private IP {address}:", address, settings)
    if not private_ips:
        logger.info("  Private IPs: none detected")
    for address in public_ips:
        _log_urls_for_host(f"Public IP {address}:", address, settings)
    if not public_ips:
        logger.info("  Public IPs: none detected")


def _request_accepts_html(request: Request) -> bool:
    return "text/html" in request.headers.get("accept", "")


def _is_browser_fallback_path(path: str) -> bool:
    return path not in {"/api", "/ui"} and not path.startswith(("/api/", "/ui/"))


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
        _log_startup_access_urls(runtime_settings)
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

    @app.exception_handler(StarletteHTTPException)
    async def http_error_handler(request: Request, exc: StarletteHTTPException) -> HTMLResponse | JSONResponse:
        if exc.status_code == 404 and _request_accepts_html(request) and _is_browser_fallback_path(request.url.path):
            return HTMLResponse(UI_PATH.read_text(encoding="utf-8"), status_code=404)
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

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
    settings = get_settings()
    uvicorn.run("app.main:app", host=settings.server_host, port=settings.server_port, reload=True)


if __name__ == "__main__":
    main()
