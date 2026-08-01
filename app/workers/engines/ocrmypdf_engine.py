from __future__ import annotations

import asyncio
import sys
import tempfile
from pathlib import Path


async def run_ocrmypdf(data: bytes, language: str, timeout_seconds: int) -> bytes:
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "input.pdf"
        output_path = Path(tmpdir) / "output.pdf"
        await asyncio.to_thread(input_path.write_bytes, data)

        process = await asyncio.create_subprocess_exec(
            sys.executable,
            "-m",
            "ocrmypdf",
            "--language",
            language,
            "--deskew",
            "--force-ocr",
            "--optimize",
            "0",
            "--quiet",
            str(input_path),
            str(output_path),
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            _, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout_seconds)
        except TimeoutError:
            process.terminate()
            try:
                await asyncio.wait_for(process.wait(), timeout=5)
            except TimeoutError:
                process.kill()
                await process.wait()
            raise

        if process.returncode != 0:
            detail = stderr.decode(errors="replace").strip()
            raise RuntimeError(detail or f"OCRmyPDF exited with status {process.returncode}.")

        return await asyncio.to_thread(output_path.read_bytes)
