import base64
import hashlib
import hmac
import json
import time
from functools import lru_cache
from typing import Annotated, Protocol

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import Cookie, Header, HTTPException, Query, Request, status

from app.core.config import settings
from app.models.security import AuthCodeClaims, Principal, PrincipalRole, TokenClaims


DEFAULT_ROLES = [
    PrincipalRole.PLATFORM_ADMIN,
    PrincipalRole.OPERATOR,
    PrincipalRole.REVIEWER,
    PrincipalRole.SUBMITTER,
]


class AuthProvider(Protocol):
    def decode(self, token: str) -> TokenClaims: ...


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def _normalize_claims(payload: dict) -> TokenClaims:
    try:
        claims = TokenClaims.model_validate(payload)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Bearer token claims are invalid") from exc
    if claims.exp is not None and claims.exp < int(time.time()):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Bearer token expired")
    if not claims.roles:
        claims.roles = [PrincipalRole.OBSERVER]
    return claims


def _int_to_b64url(value: int) -> str:
    byte_length = max(1, (value.bit_length() + 7) // 8)
    return _b64url_encode(value.to_bytes(byte_length, "big"))


class LocalTokenAuthProvider:
    @staticmethod
    def _sign(payload_segment: str) -> str:
        digest = hmac.new(settings.auth_token_secret.encode("utf-8"), payload_segment.encode("utf-8"), hashlib.sha256).digest()
        return _b64url_encode(digest)

    def decode(self, token: str) -> TokenClaims:
        try:
            prefix, payload_segment, signature = token.split(".", 2)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Malformed bearer token") from exc
        if prefix != "rgp":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unsupported bearer token")
        expected = self._sign(payload_segment)
        if not hmac.compare_digest(signature, expected):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid bearer token signature")
        try:
            payload = json.loads(_b64url_decode(payload_segment))
        except Exception as exc:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid bearer token payload") from exc
        return _normalize_claims(payload)


class LocalAuthCodeProvider:
    PREFIX = "rgpac"

    @staticmethod
    def _sign(payload_segment: str) -> str:
        digest = hmac.new(settings.auth_token_secret.encode("utf-8"), payload_segment.encode("utf-8"), hashlib.sha256).digest()
        return _b64url_encode(digest)

    @classmethod
    def encode(
        cls,
        user_id: str,
        tenant_id: str,
        roles: list[PrincipalRole],
        redirect_uri: str,
        expires_in_seconds: int = 300,
    ) -> str:
        payload = {
            "sub": user_id,
            "tenant_id": tenant_id,
            "roles": [role.value for role in roles],
            "redirect_uri": redirect_uri,
            "exp": int(time.time()) + expires_in_seconds,
        }
        payload_segment = _b64url_encode(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8"))
        signature = cls._sign(payload_segment)
        return f"{cls.PREFIX}.{payload_segment}.{signature}"

    @classmethod
    def decode(cls, token: str) -> AuthCodeClaims:
        try:
            prefix, payload_segment, signature = token.split(".", 2)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Malformed authorization code") from exc
        if prefix != cls.PREFIX:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unsupported authorization code")
        expected = cls._sign(payload_segment)
        if not hmac.compare_digest(signature, expected):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authorization code signature")
        try:
            payload = json.loads(_b64url_decode(payload_segment))
            claims = AuthCodeClaims.model_validate(payload)
        except Exception as exc:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authorization code payload") from exc
        if claims.exp is not None and claims.exp < int(time.time()):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization code expired")
        if not claims.roles:
            claims.roles = [PrincipalRole.OBSERVER]
        return claims


class JwksTokenAuthProvider:
    def __init__(self, jwks_url: str, issuer: str | None = None, audience: str | None = None) -> None:
        self.jwks_url = jwks_url
        self.issuer = issuer
        self.audience = audience
        self.jwks_client = jwt.PyJWKClient(jwks_url)

    def decode(self, token: str) -> TokenClaims:
        try:
            signing_key = self.jwks_client.get_signing_key_from_jwt(token)
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256", "ES256"],
                issuer=self.issuer,
                audience=self.audience,
                options={
                    "verify_signature": True,
                    "verify_exp": True,
                    "verify_aud": self.audience is not None,
                    "verify_iss": self.issuer is not None,
                },
            )
        except jwt.PyJWTError as exc:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid bearer token: {exc}") from exc
        return _normalize_claims(payload)


@lru_cache(maxsize=1)
def _dev_jwks_private_key():
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


def dev_jwks_document() -> dict:
    public_key = _dev_jwks_private_key().public_key().public_numbers()
    return {
        "keys": [
            {
                "kty": "RSA",
                "use": "sig",
                "alg": "RS256",
                "kid": "rgp-dev-jwks-1",
                "n": _int_to_b64url(public_key.n),
                "e": _int_to_b64url(public_key.e),
            }
        ]
    }


def encode_dev_jwks_token(
    user_id: str,
    tenant_id: str,
    roles: list[PrincipalRole],
    expires_in_seconds: int = 3600,
    issuer: str | None = None,
    audience: str | None = None,
) -> str:
    payload = {
        "sub": user_id,
        "tenant_id": tenant_id,
        "roles": [role.value for role in roles],
        "exp": int(time.time()) + expires_in_seconds,
    }
    if issuer:
        payload["iss"] = issuer
    if audience:
        payload["aud"] = audience
    return jwt.encode(
        payload,
        _dev_jwks_private_key(),
        algorithm="RS256",
        headers={"kid": "rgp-dev-jwks-1"},
    )


def encode_access_token(user_id: str, tenant_id: str, roles: list[PrincipalRole], expires_in_seconds: int = 3600) -> str:
    payload = {
        "sub": user_id,
        "tenant_id": tenant_id,
        "roles": [role.value for role in roles],
        "exp": int(time.time()) + expires_in_seconds,
    }
    payload_segment = _b64url_encode(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8"))
    signature = LocalTokenAuthProvider._sign(payload_segment)
    return f"rgp.{payload_segment}.{signature}"


def encode_auth_code(
    user_id: str,
    tenant_id: str,
    roles: list[PrincipalRole],
    redirect_uri: str,
    expires_in_seconds: int = 300,
) -> str:
    return LocalAuthCodeProvider.encode(user_id, tenant_id, roles, redirect_uri, expires_in_seconds)


def decode_auth_code(code: str) -> AuthCodeClaims:
    return LocalAuthCodeProvider.decode(code)


@lru_cache(maxsize=1)
def _auth_provider() -> AuthProvider:
    mode = settings.auth_mode.lower().strip()
    if mode == "local":
        return LocalTokenAuthProvider()
    if mode == "jwks":
        if not settings.auth_jwks_url:
            raise RuntimeError("RGP_AUTH_JWKS_URL is required when auth_mode=jwks")
        return JwksTokenAuthProvider(
            jwks_url=settings.auth_jwks_url,
            issuer=settings.auth_jwt_issuer,
            audience=settings.auth_jwt_audience,
        )
    raise RuntimeError(f"Unsupported auth mode: {settings.auth_mode}")


def decode_access_token(token: str) -> TokenClaims:
    try:
        provider = _auth_provider()
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
    return provider.decode(token)


def _default_principal() -> Principal:
    return Principal(user_id="user_demo", tenant_id="tenant_demo", roles=DEFAULT_ROLES.copy())


def _dev_fallback_allowed() -> bool:
    return settings.app_env.lower() == "development" and settings.allow_dev_auth_fallback


def get_principal(
    authorization: Annotated[str | None, Header()] = None,
    access_token: Annotated[str | None, Query()] = None,
    session_access_token: Annotated[str | None, Cookie(alias="rgp_access_token")] = None,
) -> Principal:
    token = None
    if authorization:
        scheme, _, credentials = authorization.partition(" ")
        if scheme.lower() != "bearer" or not credentials:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization header must use Bearer token")
        token = credentials
    elif access_token:
        token = access_token
    elif session_access_token:
        token = session_access_token

    if token:
        claims = decode_access_token(token)
        return Principal(user_id=claims.sub, tenant_id=claims.tenant_id, roles=claims.roles)

    if _dev_fallback_allowed():
        return _default_principal()

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Bearer token required")


def try_get_request_principal(request: Request) -> Principal | None:
    authorization = request.headers.get("authorization")
    access_token = request.query_params.get("access_token")
    session_access_token = request.cookies.get("rgp_access_token")
    token = None
    if authorization:
        scheme, _, credentials = authorization.partition(" ")
        if scheme.lower() == "bearer" and credentials:
            token = credentials
    elif access_token:
        token = access_token
    elif session_access_token:
        token = session_access_token

    if token:
        claims = decode_access_token(token)
        return Principal(user_id=claims.sub, tenant_id=claims.tenant_id, roles=claims.roles)
    if _dev_fallback_allowed():
        return _default_principal()
    return None


def ensure_roles(principal: Principal, *required_roles: PrincipalRole) -> Principal:
    principal_roles = set(principal.roles)
    effective_roles = set(principal_roles)
    if PrincipalRole.PLATFORM_ADMIN in principal_roles:
        effective_roles.update({PrincipalRole.TENANT_ADMIN, PrincipalRole.ADMIN})
    if PrincipalRole.TENANT_ADMIN in principal_roles:
        effective_roles.add(PrincipalRole.ADMIN)
    if not set(required_roles).intersection(effective_roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Requires one of roles: {', '.join(role.value for role in required_roles)}",
        )
    return principal
