from __future__ import annotations

import pytest
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient

from app.core.config import Settings
from app.main import create_app


@pytest.mark.asyncio
async def test_test_ui_is_served(tmp_path) -> None:
    settings = Settings(
        auth_provider="local",
        database_url=f"sqlite+aiosqlite:///{tmp_path / 'dococr.db'}",
        local_storage_root=tmp_path / "storage",
        auto_create_schema=True,
    )
    app = create_app(settings)

    async with (
        LifespanManager(app),
        AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client,
    ):
        response = await client.get("/ui")

    assert response.status_code == 200
    assert "Document OCR Test UI" in response.text
    assert 'const API_BASE = "/api/v1"' in response.text
