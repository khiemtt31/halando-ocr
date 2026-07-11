from __future__ import annotations

import io


def extract_image_text(data: bytes, language: str) -> list[dict[str, object]]:
    import pytesseract
    from PIL import Image

    image = Image.open(io.BytesIO(data))
    text = pytesseract.image_to_string(image, lang=language).strip()
    width, height = image.size
    return [
        {
            "page_number": 1,
            "text_content": text,
            "confidence": 100.0 if text else 0.0,
            "width": width,
            "height": height,
        }
    ]
