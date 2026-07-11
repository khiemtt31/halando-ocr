from __future__ import annotations

from app.core.auth.base import AuthProvider
from app.core.auth.keycloak import KeycloakAuthProvider
from app.core.auth.local import LocalAuthProvider
from app.core.config import Settings


def build_auth_provider(settings: Settings) -> AuthProvider:
    provider = settings.auth_provider.strip().lower()
    if provider == "keycloak":
        return KeycloakAuthProvider(settings)
    if provider == "local":
        return LocalAuthProvider(settings)
    raise ValueError(f"Unsupported AUTH_PROVIDER: {settings.auth_provider}")
