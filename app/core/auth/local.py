from __future__ import annotations

from fastapi import Request

from app.core.auth.base import Principal, clean_roles
from app.core.config import Settings


class LocalAuthProvider:
    def __init__(self, settings: Settings):
        self.settings = settings

    async def aclose(self) -> None:
        return None

    async def resolve_principal(self, request: Request) -> Principal:
        return self._demo_principal(request)

    def _demo_principal(self, request: Request) -> Principal:
        headers = request.headers
        roles = headers.get("x-demo-roles")
        parsed_roles = [role.strip() for role in roles.split(",")] if roles else self.settings.demo_roles
        return Principal(
            sub=headers.get("x-demo-sub", self.settings.demo_default_sub),
            email=headers.get("x-demo-email", self.settings.demo_default_email),
            name=headers.get("x-demo-name", self.settings.demo_default_name),
            tenant_id=headers.get("x-demo-tenant", self.settings.default_tenant_id),
            roles=clean_roles(parsed_roles),
            claims={"mode": "local-demo"},
        )
