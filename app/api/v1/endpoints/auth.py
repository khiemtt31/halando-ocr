from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_settings
from app.core.config import Settings
from app.schemas.auth import AuthConfigResponse, SeededAccountRead

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/config", response_model=AuthConfigResponse)
async def auth_config(settings: Settings = Depends(get_settings)) -> AuthConfigResponse:
    seeded_account = None
    if settings.seeded_account_enabled and settings.app_env == "local":
        seeded_account = SeededAccountRead(
            username=settings.seeded_account_username,
            password=settings.seeded_account_password,
            email=settings.seeded_account_email,
            name=settings.seeded_account_name,
        )

    if settings.auth_provider == "keycloak":
        return AuthConfigResponse(
            provider=settings.auth_provider,
            client_id=settings.keycloak_client_id,
            realm=settings.keycloak_realm,
            issuer_url=settings.keycloak_expected_issuer_url,
            authorization_url=settings.keycloak_authorization_endpoint,
            token_url=settings.keycloak_token_endpoint,
            logout_url=settings.keycloak_logout_endpoint,
            scopes=settings.keycloak_scopes,
            seeded_account=seeded_account,
        )

    return AuthConfigResponse(provider=settings.auth_provider, seeded_account=seeded_account)
