from enum import StrEnum

from pydantic import Field

from app.models.common import RgpModel


class PrincipalRole(StrEnum):
    PLATFORM_ADMIN = "platform_admin"
    TENANT_ADMIN = "tenant_admin"
    ADMIN = "admin"
    OPERATOR = "operator"
    REVIEWER = "reviewer"
    SUBMITTER = "submitter"
    OBSERVER = "observer"


class PrincipalType(StrEnum):
    USER = "user"
    MACHINE = "machine"


class Principal(RgpModel):
    user_id: str
    tenant_id: str = ""
    principal_type: PrincipalType = PrincipalType.USER
    client_id: str | None = None
    roles: list[PrincipalRole] = Field(default_factory=list)
    scopes: list[str] = Field(default_factory=list)


class TokenClaims(RgpModel):
    sub: str
    tenant_id: str | None = None
    iss: str | None = None
    aud: str | list[str] | None = None
    azp: str | None = None
    client_id: str | None = None
    scope: str | None = None
    service_account: bool | None = None
    roles: list[str] = Field(default_factory=list)
    realm_roles: list[str] = Field(default_factory=list)
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
    roles: list[PrincipalRole] = Field(default_factory=lambda: [PrincipalRole.PLATFORM_ADMIN, PrincipalRole.OPERATOR, PrincipalRole.REVIEWER, PrincipalRole.SUBMITTER])
    expires_in_seconds: int = 3600


class TokenResponse(RgpModel):
    access_token: str
    token_type: str = "bearer"


class LocalLoginRequest(RgpModel):
    email: str
    password: str
    tenant_id: str = "tenant_demo"


class DevJwksTokenRequest(DevTokenRequest):
    issuer: str | None = None
    audience: str | None = None


class DevTokenExchangeRequest(RgpModel):
    code: str
    redirect_uri: str


class PublicRegistrationRequest(RgpModel):
    display_name: str
    email: str
    organization_id: str
    job_title: str
    requested_team_id: str
    requested_roles: list[PrincipalRole] = Field(default_factory=lambda: [PrincipalRole.SUBMITTER])
    business_justification: str
    tenant_id: str = "tenant_demo"


class RegistrationSubmissionResponse(RgpModel):
    request_id: str
    status: str
    message: str


class PublicTenantOption(RgpModel):
    id: str
    name: str
    status: str = "active"


class PublicOrganizationOption(RgpModel):
    id: str
    name: str
    status: str


class PublicTeamOption(RgpModel):
    id: str
    organization_id: str
    name: str
    kind: str
    status: str


class RegistrationOptionsResponse(RgpModel):
    tenants: list[PublicTenantOption] = Field(default_factory=list)
    organizations: list[PublicOrganizationOption] = Field(default_factory=list)
    teams: list[PublicTeamOption] = Field(default_factory=list)
