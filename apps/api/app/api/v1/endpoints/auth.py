from urllib.parse import urlencode

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import RedirectResponse

from app.core.auth import decode_auth_code, dev_jwks_document, encode_access_token, encode_auth_code, encode_dev_jwks_token
from app.core.config import settings
from app.models.security import DevJwksTokenRequest, DevTokenExchangeRequest, DevTokenRequest, PrincipalRole, TokenResponse

router = APIRouter()


@router.post("/dev-token", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def issue_dev_token(payload: DevTokenRequest) -> TokenResponse:
    if settings.app_env.lower() != "development" or not settings.allow_dev_token_issuance or settings.auth_mode.lower() != "local":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Development token issuance is disabled")
    return TokenResponse(
        access_token=encode_access_token(
            user_id=payload.user_id,
            tenant_id=payload.tenant_id,
            roles=payload.roles,
            expires_in_seconds=payload.expires_in_seconds,
        )
    )


@router.get("/dev-jwks")
def get_dev_jwks() -> dict:
    if settings.app_env.lower() != "development":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Development JWKS is disabled")
    return dev_jwks_document()


@router.post("/dev-jwt", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def issue_dev_jwt(payload: DevJwksTokenRequest) -> TokenResponse:
    if settings.app_env.lower() != "development":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Development JWT issuance is disabled")
    return TokenResponse(
        access_token=encode_dev_jwks_token(
            user_id=payload.user_id,
            tenant_id=payload.tenant_id,
            roles=payload.roles,
            expires_in_seconds=payload.expires_in_seconds,
            issuer=payload.issuer,
            audience=payload.audience,
        )
    )


@router.get("/dev-authorize")
def dev_authorize(
    redirect_uri: str,
    state: str,
    user_id: str = Query(default="user_demo"),
    tenant_id: str = Query(default="tenant_demo"),
    roles: list[PrincipalRole] = Query(default=[PrincipalRole.ADMIN, PrincipalRole.OPERATOR, PrincipalRole.REVIEWER, PrincipalRole.SUBMITTER]),
) -> RedirectResponse:
    if settings.app_env.lower() != "development" or not settings.allow_dev_token_issuance or settings.auth_mode.lower() != "local":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Development authorization is disabled")
    if redirect_uri not in {f"{origin}/login/callback" for origin in settings.cors_origins}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Redirect URI is not allowed")
    code = encode_auth_code(
        user_id=user_id,
        tenant_id=tenant_id,
        roles=roles,
        redirect_uri=redirect_uri,
    )
    return RedirectResponse(url=f"{redirect_uri}?{urlencode({'code': code, 'state': state})}", status_code=status.HTTP_307_TEMPORARY_REDIRECT)


@router.post("/dev-exchange", response_model=TokenResponse, status_code=status.HTTP_200_OK)
def exchange_dev_code(payload: DevTokenExchangeRequest) -> TokenResponse:
    if settings.app_env.lower() != "development" or not settings.allow_dev_token_issuance or settings.auth_mode.lower() != "local":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Development token exchange is disabled")
    claims = decode_auth_code(payload.code)
    if claims.redirect_uri != payload.redirect_uri:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Authorization code redirect URI mismatch")
    return TokenResponse(
        access_token=encode_access_token(
            user_id=claims.sub,
            tenant_id=claims.tenant_id,
            roles=claims.roles,
            expires_in_seconds=3600,
        )
    )
