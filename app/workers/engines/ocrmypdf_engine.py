from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path


async def run_ocrmypdf(data: bytes, language: str, timeout_seconds: int) -> bytes:
    import ocrmypdf

    def _run() -> bytes:
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.pdf"
            output_path = Path(tmpdir) / "output.pdf"
            input_path.write_bytes(data)
            ocrmypdf.ocr(
                input_path,
                output_path,
                language=language,
                deskew=True,
                force_ocr=True,
                optimize=0,
                progress_bar=False,
            )
            return output_path.read_bytes()

    return await asyncio.wait_for(asyncio.to_thread(_run), timeout=timeout_seconds)
