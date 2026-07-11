from __future__ import annotations

import pytest

from app.services.storage import LocalStorageBackend


@pytest.mark.asyncio
async def test_local_storage_save_read_exists_and_delete(tmp_path) -> None:
    storage = LocalStorageBackend(tmp_path)
    key = "tenants/default/users/demo/documents/doc-1/original/sample.txt"

    await storage.save_bytes(key, b"hello", "text/plain")

    assert await storage.exists(key) is True
    assert await storage.read_bytes(key) == b"hello"

    await storage.delete(key)

    assert await storage.exists(key) is False


@pytest.mark.asyncio
async def test_local_storage_rejects_keys_outside_root(tmp_path) -> None:
    storage = LocalStorageBackend(tmp_path)

    with pytest.raises(ValueError, match="escapes"):
        await storage.save_bytes("../outside.txt", b"unsafe")
