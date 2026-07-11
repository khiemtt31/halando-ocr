from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class APIError(Exception):
    code: str
    message: str
    status_code: int = 400

    def __str__(self) -> str:
        return f"{self.code}: {self.message}"


def error_response(request_id: str, code: str, message: str) -> dict[str, dict[str, str]]:
    return {"error": {"code": code, "message": message, "request_id": request_id}}
