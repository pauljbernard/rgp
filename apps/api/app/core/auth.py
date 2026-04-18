import base64
import hashlib
import hmac
import json
import time
from functools import lru_cache
from typing import Annotated, Protocol

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import Cookie, Header, HTTPException, Query, Request, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings
from app.models.security import AuthCodeClaims, Principal, PrincipalRole, PrincipalType, TokenClaims

TENANT_HEADER_NAME = "x-tenant-id"
TENANT_COOKIE_NAME = "rgp_tenant_id"
http_bearer = HTTPBearer(
    auto_error=False,
    description="Shared IDP bearer token for RGP user or machine authentication.",
)

DEFAULT_ROLES = [
    PrincipalRole.PLATFORM_ADMIN,
    PrincipalRole.OPERATOR,
    PrincipalRole.REVIEWER,
    PrincipalRole.SUBMITTER,
]


class AuthProvider(Protocol):
    def decode(self, token: str) -> TokenClaims: ...


def _normalized_auth_mode() -> str:
    return settings.auth_mode.lower().strip()


def auth_mode_supports_local() -> bool:
    return _normalized_auth_mode() in {"local", "hybrid", "local+jwks", "jwks+local", "mixed"}


def auth_mode_supports_jwks() -> bool:
    return _normalized_auth_mode() in {"jwks", "hybrid", "local+jwks", "jwks+local", "mixed"}


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
    return claims


def _scope_names(claims: TokenClaims) -> list[str]:
    return [scope for scope in (claims.scope or "").split() if scope]


def _claim_audiences(claims: TokenClaims) -> list[str]:
    if isinstance(claims.aud, str):
        return [claims.aud]
    return [audience for audience in (claims.aud or []) if isinstance(audience, str)]


def _machine_audiences() -> set[str]:
    return {
        audience.strip()
        for audience in [settings.auth_machine_jwt_audience]
        if isinstance(audience, str) and audience.strip()
    }


def _trusted_machine_client_ids() -> set[str]:
    return {client_id.strip() for client_id in settings.auth_trusted_machine_client_ids if client_id.strip()}


def _principal_type(claims: TokenClaims) -> PrincipalType:
    if claims.service_account is True:
        return PrincipalType.MACHINE
    if _machine_audiences() & set(_claim_audiences(claims)):
        return PrincipalType.MACHINE
    if claims.azp and claims.azp in _trusted_machine_client_ids():
        return PrincipalType.MACHINE
    return PrincipalType.USER


def _normalized_principal_roles(claims: TokenClaims, principal_type: PrincipalType) -> list[PrincipalRole]:
    raw_roles = [str(role).strip() for role in [*claims.roles, *claims.realm_roles] if str(role).strip()]
    mapped_roles: list[PrincipalRole] = []
    for raw_role in raw_roles:
        normalized = raw_role.strip().lower()
        if normalized in {"platform_admin", "platform-admin", "realm-admin"}:
            mapped_roles.append(PrincipalRole.PLATFORM_ADMIN)
        elif normalized in {"tenant_admin", "tenant-admin", "application-admin"}:
            mapped_roles.append(PrincipalRole.TENANT_ADMIN)
        elif normalized in {"admin", "workflow-service-admin"}:
            mapped_roles.append(PrincipalRole.ADMIN)
        elif normalized in {"operator", "tenant-operator", "workflow-operator", "workflow-service-writer"}:
            mapped_roles.append(PrincipalRole.OPERATOR)
        elif normalized in {"reviewer"}:
            mapped_roles.append(PrincipalRole.REVIEWER)
        elif normalized in {"submitter"}:
            mapped_roles.append(PrincipalRole.SUBMITTER)
        elif normalized in {"observer", "viewer", "workflow-service-reader"}:
            mapped_roles.append(PrincipalRole.OBSERVER)
    if not mapped_roles:
        return [PrincipalRole.OBSERVER]
    return list(dict.fromkeys(mapped_roles))


def _resolved_client_id(claims: TokenClaims) -> str | None:
    client_id = claims.client_id or claims.azp
    return client_id.strip() if isinstance(client_id, str) and client_id.strip() else None


def _resolved_tenant_id(claims: TokenClaims, explicit_tenant_id: str | None, principal_roles: list[PrincipalRole]) -> str:
    if claims.tenant_id and claims.tenant_id.strip():
        return claims.tenant_id.strip()
    if explicit_tenant_id and explicit_tenant_id.strip():
        return explicit_tenant_id.strip()
    if PrincipalRole.PLATFORM_ADMIN in principal_roles:
        return ""
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Tenant context is required when bearer token does not include tenant_id",
    )


def _principal_from_claims(claims: TokenClaims, explicit_tenant_id: str | None = None) -> Principal:
    principal_type = _principal_type(claims)
    client_id = _resolved_client_id(claims)
    if principal_type == PrincipalType.MACHINE and _trusted_machine_client_ids() and client_id not in _trusted_machine_client_ids():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Machine token client is not trusted")
    principal_roles = _normalized_principal_roles(claims, principal_type)
    return Principal(
        user_id=claims.sub,
        tenant_id=_resolved_tenant_id(claims, explicit_tenant_id, principal_roles),
        principal_type=principal_type,
        client_id=client_id,
        roles=principal_roles,
        scopes=_scope_names(claims),
    )


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
    def __init__(self, jwks_url: str, issuer: str | None = None, audiences: list[str] | None = None) -> None:
        self.jwks_url = jwks_url
        self.issuer = issuer
        self.audiences = [audience for audience in (audiences or []) if audience]
        self.jwks_client = jwt.PyJWKClient(jwks_url)

    def decode(self, token: str) -> TokenClaims:
        last_error: jwt.PyJWTError | None = None
        try:
            signing_key = self.jwks_client.get_signing_key_from_jwt(token)
        except jwt.PyJWTError as exc:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid bearer token: {exc}") from exc
        for audience in self.audiences or [None]:
            try:
                payload = jwt.decode(
                    token,
                    signing_key.key,
                    algorithms=["RS256", "ES256"],
                    issuer=self.issuer,
                    audience=audience,
                    options={
                        "verify_signature": True,
                        "verify_exp": True,
                        "verify_aud": audience is not None,
                        "verify_iss": self.issuer is not None,
                    },
                )
                return _normalize_claims(payload)
            except jwt.PyJWTError as exc:
                last_error = exc
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid bearer token: {last_error}") from last_error


class CombinedTokenAuthProvider:
    def __init__(self, local_provider: LocalTokenAuthProvider, jwks_provider: JwksTokenAuthProvider) -> None:
        self.local_provider = local_provider
        self.jwks_provider = jwks_provider

    def decode(self, token: str) -> TokenClaims:
        providers = [self.local_provider, self.jwks_provider] if token.startswith("rgp.") else [self.jwks_provider, self.local_provider]
        last_error: HTTPException | None = None
        for provider in providers:
            try:
                return provider.decode(token)
            except HTTPException as exc:
                last_error = exc
        if last_error:
            raise last_error
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Bearer token is invalid")


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
    if auth_mode_supports_local() and not auth_mode_supports_jwks():
        return LocalTokenAuthProvider()
    if auth_mode_supports_jwks():
        if not settings.auth_jwks_url:
            raise RuntimeError("RGP_AUTH_JWKS_URL is required when auth_mode=jwks")
        audiences = [
            audience
            for audience in [
                settings.auth_user_jwt_audience or settings.auth_jwt_audience,
                settings.auth_machine_jwt_audience,
            ]
            if audience
        ]
        jwks_provider = JwksTokenAuthProvider(
            jwks_url=settings.auth_jwks_url,
            issuer=settings.auth_jwt_issuer,
            audiences=audiences,
        )
        if auth_mode_supports_local():
            return CombinedTokenAuthProvider(LocalTokenAuthProvider(), jwks_provider)
        return jwks_provider
    raise RuntimeError(f"Unsupported auth mode: {settings.auth_mode}")


def decode_access_token(token: str) -> TokenClaims:
    try:
        provider = _auth_provider()
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
    return provider.decode(token)


def _default_principal() -> Principal:
    return Principal(user_id="user_demo", tenant_id="tenant_demo", roles=DEFAULT_ROLES.copy(), principal_type=PrincipalType.USER)


def _dev_fallback_allowed() -> bool:
    return settings.app_env.lower() == "development" and settings.allow_dev_auth_fallback


def get_principal(
    bearer_credentials: Annotated[HTTPAuthorizationCredentials | None, Security(http_bearer)] = None,
    access_token: Annotated[str | None, Query()] = None,
    session_access_token: Annotated[str | None, Cookie(alias="rgp_access_token")] = None,
    selected_tenant_id: Annotated[
        str | None,
        Header(
            alias=TENANT_HEADER_NAME,
            description="Tenant context override. Required when the bearer token does not include a tenant_id claim.",
        ),
    ] = None,
    selected_tenant_query: Annotated[str | None, Query(alias="tenant_id")] = None,
    tenant_cookie: Annotated[str | None, Cookie(alias=TENANT_COOKIE_NAME)] = None,
) -> Principal:
    token = None
    explicit_tenant_id = selected_tenant_id or selected_tenant_query or tenant_cookie
    if bearer_credentials:
        if bearer_credentials.scheme.lower() != "bearer" or not bearer_credentials.credentials:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization header must use Bearer token")
        token = bearer_credentials.credentials
    elif access_token:
        token = access_token
    elif session_access_token:
        token = session_access_token

    if token:
        claims = decode_access_token(token)
        return _principal_from_claims(claims, explicit_tenant_id)

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
        explicit_tenant_id = request.headers.get(TENANT_HEADER_NAME) or request.query_params.get("tenant_id") or request.cookies.get(TENANT_COOKIE_NAME)
        return _principal_from_claims(claims, explicit_tenant_id)
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


def ensure_user_principal(principal: Principal) -> Principal:
    if principal.principal_type != PrincipalType.USER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User principal required")
    return principal


def ensure_machine_principal(principal: Principal) -> Principal:
    if principal.principal_type != PrincipalType.MACHINE:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Machine principal required")
    return principal


def ensure_machine_scopes(principal: Principal, *required_scopes: str) -> Principal:
    ensure_machine_principal(principal)
    granted = set(principal.scopes)
    if not set(required_scopes).issubset(granted):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Requires scopes: {', '.join(required_scopes)}",
        )
    return principal
