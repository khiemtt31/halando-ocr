from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class PrincipalRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    sub: str
    email: str | None = None
    name: str | None = None
    tenant_id: str = "default"
    roles: list[str] = Field(default_factory=list)


class MeResponse(PrincipalRead):
    user_id: str | None = None
    status: str = "active"


class SeededAccountRead(BaseModel):
    username: str
    password: str
    email: str
    name: str


class AuthConfigResponse(BaseModel):
    provider: str
    client_id: str | None = None
    realm: str | None = None
    issuer_url: str | None = None
    authorization_url: str | None = None
    token_url: str | None = None
    logout_url: str | None = None
    scopes: str = "openid profile email"
    seeded_account: SeededAccountRead | None = None
