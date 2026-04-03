from enum import StrEnum

from pydantic import Field

from app.models.common import RgpModel


class PrincipalRole(StrEnum):
    ADMIN = "admin"
    OPERATOR = "operator"
    REVIEWER = "reviewer"
    SUBMITTER = "submitter"
    OBSERVER = "observer"


class Principal(RgpModel):
    user_id: str
    tenant_id: str
    roles: list[PrincipalRole] = Field(default_factory=list)


class TokenClaims(RgpModel):
    sub: str
    tenant_id: str
    roles: list[PrincipalRole] = Field(default_factory=list)
    exp: int | None = None


class AuthCodeClaims(RgpModel):
    sub: str
    tenant_id: str
    roles: list[PrincipalRole] = Field(default_factory=list)
    redirect_uri: str
    exp: int | None = None


class DevTokenRequest(RgpModel):
    user_id: str = "user_demo"
    tenant_id: str = "tenant_demo"
    roles: list[PrincipalRole] = Field(default_factory=lambda: [PrincipalRole.ADMIN, PrincipalRole.OPERATOR, PrincipalRole.REVIEWER, PrincipalRole.SUBMITTER])
    expires_in_seconds: int = 3600


class TokenResponse(RgpModel):
    access_token: str
    token_type: str = "bearer"


class DevJwksTokenRequest(DevTokenRequest):
    issuer: str | None = None
    audience: str | None = None


class DevTokenExchangeRequest(RgpModel):
    code: str
    redirect_uri: str
