from urllib.parse import urlencode

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse

from app.core.auth import decode_auth_code, dev_jwks_document, encode_access_token, encode_auth_code, encode_dev_jwks_token, get_principal
from app.core.config import settings
from app.models.security import DevJwksTokenRequest, DevTokenExchangeRequest, DevTokenRequest, LocalLoginRequest, Principal, PrincipalRole, PublicOrganizationOption, PublicRegistrationRequest, PublicTeamOption, PublicTenantOption, RegistrationOptionsResponse, RegistrationSubmissionResponse, TokenResponse
from app.services.governance_service import governance_service

router = APIRouter()


@router.get("/me", response_model=Principal, status_code=status.HTTP_200_OK)
def get_current_principal(principal: Annotated[Principal, Depends(get_principal)]) -> Principal:
    return principal


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
    roles: list[PrincipalRole] = Query(default=[PrincipalRole.PLATFORM_ADMIN, PrincipalRole.OPERATOR, PrincipalRole.REVIEWER, PrincipalRole.SUBMITTER]),
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


@router.post("/local-login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
def local_login(payload: LocalLoginRequest) -> TokenResponse:
    if settings.auth_mode.lower() != "local":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Local credential login is disabled")
    try:
        principal = governance_service.authenticate_local_user(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    return TokenResponse(
        access_token=encode_access_token(
            user_id=principal.user_id,
            tenant_id=principal.tenant_id,
            roles=principal.roles,
            expires_in_seconds=3600,
        )
    )


@router.post("/register", response_model=RegistrationSubmissionResponse, status_code=status.HTTP_201_CREATED)
def create_registration_request(payload: PublicRegistrationRequest) -> RegistrationSubmissionResponse:
    try:
        return governance_service.create_public_registration_request(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.get("/registration-options", response_model=RegistrationOptionsResponse, status_code=status.HTTP_200_OK)
def get_registration_options(tenant_id: str = Query(default="tenant_demo")) -> RegistrationOptionsResponse:
    tenant_options = governance_service.list_tenants(Principal(user_id="registration_portal", tenant_id=tenant_id, roles=[PrincipalRole.PLATFORM_ADMIN]))
    organizations = governance_service.list_organizations(Principal(user_id="registration_portal", tenant_id=tenant_id, roles=[]))
    teams = governance_service.list_public_registration_teams(tenant_id)
    return RegistrationOptionsResponse(
        tenants=[PublicTenantOption(id=tenant.id, name=tenant.name, status=tenant.status) for tenant in tenant_options if tenant.status == "active"],
        organizations=[PublicOrganizationOption(id=organization.id, name=organization.name, status=organization.status) for organization in organizations if organization.status == "active"],
        teams=[
            PublicTeamOption(
                id=team.id,
                organization_id=team.organization_id,
                name=team.name,
                kind=team.kind,
                status=team.status,
            )
            for team in teams
            if team.status == "active"
        ],
    )
