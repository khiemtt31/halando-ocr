from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Protocol

from fastapi import Request
from pydantic import BaseModel, ConfigDict, Field


class Principal(BaseModel):
    model_config = ConfigDict(extra="ignore")

    sub: str
    email: str | None = None
    name: str | None = None
    tenant_id: str = "default"
    roles: list[str] = Field(default_factory=list)
    claims: dict[str, Any] = Field(default_factory=dict)

    @property
    def is_admin(self) -> bool:
        return "admin:manage" in self.roles


class AuthProvider(Protocol):
    async def aclose(self) -> None:
        ...

    async def resolve_principal(self, request: Request) -> Principal:
        ...


def clean_roles(values: list[str]) -> list[str]:
    return sorted({value.strip() for value in values if value and value.strip()})


def _extend_roles(roles: list[str], value: object) -> None:
    if isinstance(value, list):
        roles.extend(str(role) for role in value)


def extract_roles(claims: Mapping[str, Any], *, client_id: str | None = None) -> list[str]:
    roles: list[str] = []

    realm_access = claims.get("realm_access") or {}
    if isinstance(realm_access, Mapping):
        _extend_roles(roles, realm_access.get("roles"))

    resource_access = claims.get("resource_access") or {}
    if client_id and isinstance(resource_access, Mapping):
        client_access = resource_access.get(client_id) or {}
        if isinstance(client_access, Mapping):
            _extend_roles(roles, client_access.get("roles"))

    scope = claims.get("scope")
    if isinstance(scope, str):
        roles.extend(scope.split())

    return clean_roles(roles)
