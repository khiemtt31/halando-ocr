from __future__ import annotations

import io


def extract_pdf_text(data: bytes, max_pages: int) -> list[dict[str, object]]:
    import pdfplumber

    pages: list[dict[str, object]] = []
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        for index, page in enumerate(pdf.pages[:max_pages], start=1):
            text = page.extract_text() or ""
            pages.append(
                {
                    "page_number": index,
                    "text_content": text.strip(),
                    "confidence": 100.0 if text.strip() else 0.0,
                    "width": int(page.width) if page.width else None,
                    "height": int(page.height) if page.height else None,
                }
            )
    return pages
