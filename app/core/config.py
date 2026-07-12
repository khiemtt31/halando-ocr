from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "doc-ocr-api"
    app_env: str = "local"
    server_host: str = "0.0.0.0"
    server_port: int = 8000
    secret_key: str = "change-me-now"
    auth_provider: Literal["local", "keycloak"] = "local"

    database_url: str = "sqlite+aiosqlite:////app/data/dococr.db"
    local_storage_root: Path = Path("/app/data/storage")

    demo_default_roles: str = "documents:read,documents:write,documents:delete,jobs:read,jobs:run"
    demo_default_sub: str = "demo-user"
    demo_default_email: str = "demo@example.com"
    demo_default_name: str = "Demo User"

    keycloak_server_url: str = "http://localhost:8080"
    keycloak_public_server_url: str = "http://localhost:8080"
    keycloak_realm: str = "halando"
    keycloak_client_id: str = "halando-api"
    keycloak_audience: str = "halando-api"
    keycloak_issuer: str | None = None
    keycloak_jwks_url: str | None = None
    keycloak_algorithms: str = "RS256"
    keycloak_scopes: str = "openid profile email"
    keycloak_jwks_cache_seconds: int = 300
    keycloak_http_timeout_seconds: float = 5.0

    seeded_account_enabled: bool = True
    seeded_account_sub: str = "00000000-0000-4000-8000-000000000001"
    seeded_account_username: str = "demo"
    seeded_account_password: str = "demo123!"
    seeded_account_email: str = "demo@halando.local"
    seeded_account_name: str = "Demo User"

    max_upload_size_mb: int = 25
    upload_url_ttl_seconds: int = 900
    download_url_ttl_seconds: int = 900
    auto_create_schema: bool = True

    ocr_default_language: str = "eng"
    ocr_timeout_seconds: int = 300
    ocr_max_pages: int = 50
    worker_poll_interval_seconds: float = 2.0

    cors_allow_origins: str = "*"
    default_tenant_id: str = "default"

    @field_validator("database_url")
    @classmethod
    def normalize_sqlite_url(cls, value: str) -> str:
        if value.startswith("sqlite:///") and "+aiosqlite" not in value:
            return value.replace("sqlite:///", "sqlite+aiosqlite:///", 1)
        return value

    @field_validator("auth_provider", mode="before")
    @classmethod
    def normalize_auth_provider(cls, value: str) -> str:
        return str(value).strip().lower()

    @property
    def max_upload_size_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024

    @property
    def demo_roles(self) -> list[str]:
        return [role.strip() for role in self.demo_default_roles.split(",") if role.strip()]

    @property
    def keycloak_server_base_url(self) -> str:
        return self.keycloak_server_url.rstrip("/")

    @property
    def keycloak_public_server_base_url(self) -> str:
        return self.keycloak_public_server_url.rstrip("/")

    @property
    def keycloak_realm_url(self) -> str:
        return f"{self.keycloak_server_base_url}/realms/{self.keycloak_realm}"

    @property
    def keycloak_public_realm_url(self) -> str:
        return f"{self.keycloak_public_server_base_url}/realms/{self.keycloak_realm}"

    @property
    def keycloak_expected_issuer_url(self) -> str:
        return (self.keycloak_issuer or self.keycloak_public_realm_url).rstrip("/")

    @property
    def keycloak_jwks_endpoint(self) -> str:
        return self.keycloak_jwks_url or f"{self.keycloak_realm_url}/protocol/openid-connect/certs"

    @property
    def keycloak_authorization_endpoint(self) -> str:
        return f"{self.keycloak_public_realm_url}/protocol/openid-connect/auth"

    @property
    def keycloak_token_endpoint(self) -> str:
        return f"{self.keycloak_public_realm_url}/protocol/openid-connect/token"

    @property
    def keycloak_logout_endpoint(self) -> str:
        return f"{self.keycloak_public_realm_url}/protocol/openid-connect/logout"

    @property
    def keycloak_algorithms_list(self) -> list[str]:
        return [algorithm.strip() for algorithm in self.keycloak_algorithms.split(",") if algorithm.strip()]

    @property
    def cors_allow_origins_list(self) -> list[str]:
        if self.cors_allow_origins.strip() == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_allow_origins.split(",") if origin.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
