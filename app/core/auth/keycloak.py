from __future__ import annotations

import time
from typing import Any

import httpx
import jwt
from fastapi import Request

from app.core.auth.base import Principal, extract_roles
from app.core.config import Settings
from app.core.errors import APIError


class KeycloakAuthProvider:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._client = httpx.AsyncClient(timeout=settings.keycloak_http_timeout_seconds)
        self._keys: dict[str, Any] = {}
        self._keys_expires_at = 0.0

    async def aclose(self) -> None:
        await self._client.aclose()

    async def resolve_principal(self, request: Request) -> Principal:
        token = self._bearer_token(request.headers.get("authorization"))
        claims = await self._decode_token(token)
        return self._principal_from_claims(claims)

    def _bearer_token(self, authorization: str | None) -> str:
        if not authorization:
            raise APIError("AUTH_UNAUTHORIZED", "Missing bearer token.", 401)
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() != "bearer" or not token.strip():
            raise APIError("AUTH_UNAUTHORIZED", "Invalid authorization header.", 401)
        return token.strip()

    async def _decode_token(self, token: str) -> dict[str, Any]:
        try:
            header = jwt.get_unverified_header(token)
        except jwt.PyJWTError as exc:
            raise APIError("AUTH_UNAUTHORIZED", "Invalid access token header.", 401) from exc

        kid = header.get("kid")
        if not kid:
            raise APIError("AUTH_UNAUTHORIZED", "Access token is missing a signing key id.", 401)

        key = await self._signing_key(str(kid))
        try:
            return jwt.decode(
                token,
                key=key,
                algorithms=self.settings.keycloak_algorithms_list,
                audience=self.settings.keycloak_audience or None,
                issuer=self.settings.keycloak_expected_issuer_url,
                options={
                    "require": ["exp", "iss", "sub"],
                    "verify_aud": bool(self.settings.keycloak_audience),
                },
            )
        except jwt.ExpiredSignatureError as exc:
            raise APIError("AUTH_UNAUTHORIZED", "Access token has expired.", 401) from exc
        except jwt.InvalidTokenError as exc:
            raise APIError("AUTH_UNAUTHORIZED", "Access token is invalid.", 401) from exc

    async def _signing_key(self, kid: str) -> Any:
        if time.monotonic() >= self._keys_expires_at or kid not in self._keys:
            await self._refresh_jwks()
        key = self._keys.get(kid)
        if key is None:
            await self._refresh_jwks()
            key = self._keys.get(kid)
        if key is None:
            raise APIError("AUTH_UNAUTHORIZED", "Access token signing key is unknown.", 401)
        return key

    async def _refresh_jwks(self) -> None:
        try:
            response = await self._client.get(self.settings.keycloak_jwks_endpoint)
            response.raise_for_status()
            jwks = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise APIError("AUTH_PROVIDER_UNAVAILABLE", "Keycloak signing keys are unavailable.", 503) from exc

        keys: dict[str, Any] = {}
        for raw_key in jwks.get("keys", []):
            if not isinstance(raw_key, dict):
                continue
            key_id = raw_key.get("kid")
            if not key_id:
                continue
            try:
                keys[str(key_id)] = jwt.PyJWK.from_dict(raw_key).key
            except jwt.PyJWKError as exc:
                raise APIError("AUTH_PROVIDER_UNAVAILABLE", "Keycloak signing key is invalid.", 503) from exc

        if not keys:
            raise APIError("AUTH_PROVIDER_UNAVAILABLE", "Keycloak did not publish signing keys.", 503)

        self._keys = keys
        self._keys_expires_at = time.monotonic() + self.settings.keycloak_jwks_cache_seconds

    def _principal_from_claims(self, claims: dict[str, Any]) -> Principal:
        name = (
            claims.get("name")
            or " ".join(part for part in [claims.get("given_name"), claims.get("family_name")] if part)
            or claims.get("preferred_username")
        )
        tenant_id = claims.get("tenant_id") or claims.get("tenant") or self.settings.default_tenant_id
        return Principal(
            sub=str(claims["sub"]),
            email=str(claims["email"]) if claims.get("email") else None,
            name=str(name) if name else None,
            tenant_id=str(tenant_id),
            roles=extract_roles(claims, client_id=self.settings.keycloak_client_id),
            claims=claims,
        )
