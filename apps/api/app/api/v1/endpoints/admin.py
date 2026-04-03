from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.auth import ensure_roles, get_principal
from app.models.governance import AddTeamMembershipRequest, CreateIntegrationRequest, CreatePortfolioRequest, CreateTeamRequest, CreateUserRequest, IntegrationRecord, PolicyRecord, PolicyRuleUpdateRequest, PortfolioRecord, TeamRecord, UpdateIntegrationRequest, UpdateTeamRequest, UpdateUserRequest, UserRecord
from app.models.security import Principal, PrincipalRole
from app.models.template import CreateTemplateVersionRequest, TemplateRecord, TemplateStatusActionRequest, TemplateValidationResult, UpdateTemplateDefinitionRequest
from app.services.template_service import template_service
from app.services.governance_service import governance_service

router = APIRouter()


@router.get("/templates", response_model=list[TemplateRecord])
def list_templates_admin(principal: Annotated[Principal, Depends(get_principal)]) -> list[TemplateRecord]:
    ensure_roles(principal, PrincipalRole.ADMIN)
    return template_service.list_admin_templates(principal)


@router.post("/templates/versions", response_model=TemplateRecord, status_code=status.HTTP_201_CREATED)
def create_template_version(
    payload: CreateTemplateVersionRequest,
    principal: Annotated[Principal, Depends(get_principal)],
) -> TemplateRecord:
    ensure_roles(principal, PrincipalRole.ADMIN)
    try:
        return template_service.create_template_version(payload, principal)
    except StopIteration:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source template version not found") from None
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.put("/templates/{template_id}/versions/{version}", response_model=TemplateRecord, status_code=status.HTTP_200_OK)
def update_template_definition(
    template_id: str,
    version: str,
    payload: UpdateTemplateDefinitionRequest,
    principal: Annotated[Principal, Depends(get_principal)],
) -> TemplateRecord:
    ensure_roles(principal, PrincipalRole.ADMIN)
    try:
        return template_service.update_template_definition(template_id, version, payload, principal)
    except StopIteration:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template version not found") from None
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.post("/templates/{template_id}/versions/{version}/validate", response_model=TemplateValidationResult, status_code=status.HTTP_200_OK)
def validate_template_definition(
    template_id: str,
    version: str,
    principal: Annotated[Principal, Depends(get_principal)],
) -> TemplateValidationResult:
    ensure_roles(principal, PrincipalRole.ADMIN)
    try:
        return template_service.validate_template_definition(template_id, version, principal)
    except StopIteration:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template version not found") from None


@router.post("/templates/{template_id}/versions/{version}/publish", response_model=TemplateRecord, status_code=status.HTTP_200_OK)
def publish_template_version(
    template_id: str,
    version: str,
    payload: TemplateStatusActionRequest,
    principal: Annotated[Principal, Depends(get_principal)],
) -> TemplateRecord:
    ensure_roles(principal, PrincipalRole.ADMIN)
    try:
        return template_service.publish_template_version(template_id, version, payload, principal)
    except StopIteration:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template version not found") from None


@router.post("/templates/{template_id}/versions/{version}/deprecate", response_model=TemplateRecord, status_code=status.HTTP_200_OK)
def deprecate_template_version(
    template_id: str,
    version: str,
    payload: TemplateStatusActionRequest,
    principal: Annotated[Principal, Depends(get_principal)],
) -> TemplateRecord:
    ensure_roles(principal, PrincipalRole.ADMIN)
    try:
        return template_service.deprecate_template_version(template_id, version, payload, principal)
    except StopIteration:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template version not found") from None


@router.delete("/templates/{template_id}/versions/{version}", status_code=status.HTTP_204_NO_CONTENT)
def delete_template_version(
    template_id: str,
    version: str,
    principal: Annotated[Principal, Depends(get_principal)],
) -> None:
    ensure_roles(principal, PrincipalRole.ADMIN)
    try:
        template_service.delete_template_version(template_id, version, principal)
    except StopIteration:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template version not found") from None
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.get("/policies", response_model=list[PolicyRecord])
def list_policies(principal: Annotated[Principal, Depends(get_principal)]) -> list[PolicyRecord]:
    ensure_roles(principal, PrincipalRole.ADMIN)
    return governance_service.list_policies(principal)


@router.put("/policies/{policy_id}/rules", response_model=PolicyRecord, status_code=status.HTTP_200_OK)
def update_policy_rules(
    policy_id: str,
    payload: PolicyRuleUpdateRequest,
    principal: Annotated[Principal, Depends(get_principal)],
) -> PolicyRecord:
    ensure_roles(principal, PrincipalRole.ADMIN)
    try:
        return governance_service.update_policy_rules(policy_id, payload, principal)
    except StopIteration:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy not found") from None
    except PermissionError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Policy not accessible for tenant") from None
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/integrations", response_model=list[IntegrationRecord])
def list_integrations(principal: Annotated[Principal, Depends(get_principal)]) -> list[IntegrationRecord]:
    ensure_roles(principal, PrincipalRole.ADMIN)
    return governance_service.list_integrations(principal)


@router.post("/integrations", response_model=IntegrationRecord, status_code=status.HTTP_201_CREATED)
def create_integration(
    payload: CreateIntegrationRequest,
    principal: Annotated[Principal, Depends(get_principal)],
) -> IntegrationRecord:
    ensure_roles(principal, PrincipalRole.ADMIN)
    try:
        return governance_service.create_integration(payload, principal)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.put("/integrations/{integration_id}", response_model=IntegrationRecord, status_code=status.HTTP_200_OK)
def update_integration(
    integration_id: str,
    payload: UpdateIntegrationRequest,
    principal: Annotated[Principal, Depends(get_principal)],
) -> IntegrationRecord:
    ensure_roles(principal, PrincipalRole.ADMIN)
    try:
        return governance_service.update_integration(integration_id, payload, principal)
    except StopIteration:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Integration not found") from None


@router.delete("/integrations/{integration_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_integration(
    integration_id: str,
    principal: Annotated[Principal, Depends(get_principal)],
) -> None:
    ensure_roles(principal, PrincipalRole.ADMIN)
    try:
        governance_service.delete_integration(integration_id, principal)
    except StopIteration:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Integration not found") from None


@router.get("/org/users", response_model=list[UserRecord])
def list_org_users(principal: Annotated[Principal, Depends(get_principal)]) -> list[UserRecord]:
    ensure_roles(principal, PrincipalRole.ADMIN)
    return governance_service.list_users(principal)


@router.post("/org/users", response_model=UserRecord, status_code=status.HTTP_201_CREATED)
def create_org_user(
    payload: CreateUserRequest,
    principal: Annotated[Principal, Depends(get_principal)],
) -> UserRecord:
    ensure_roles(principal, PrincipalRole.ADMIN)
    try:
        return governance_service.create_user(payload, principal)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.put("/org/users/{user_id}", response_model=UserRecord, status_code=status.HTTP_200_OK)
def update_org_user(
    user_id: str,
    payload: UpdateUserRequest,
    principal: Annotated[Principal, Depends(get_principal)],
) -> UserRecord:
    ensure_roles(principal, PrincipalRole.ADMIN)
    try:
        return governance_service.update_user(user_id, payload, principal)
    except StopIteration:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found") from None


@router.get("/org/teams", response_model=list[TeamRecord])
def list_org_teams(principal: Annotated[Principal, Depends(get_principal)]) -> list[TeamRecord]:
    ensure_roles(principal, PrincipalRole.ADMIN)
    return governance_service.list_teams(principal)


@router.post("/org/teams", response_model=TeamRecord, status_code=status.HTTP_201_CREATED)
def create_org_team(
    payload: CreateTeamRequest,
    principal: Annotated[Principal, Depends(get_principal)],
) -> TeamRecord:
    ensure_roles(principal, PrincipalRole.ADMIN)
    try:
        return governance_service.create_team(payload, principal)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.put("/org/teams/{team_id}", response_model=TeamRecord, status_code=status.HTTP_200_OK)
def update_org_team(
    team_id: str,
    payload: UpdateTeamRequest,
    principal: Annotated[Principal, Depends(get_principal)],
) -> TeamRecord:
    ensure_roles(principal, PrincipalRole.ADMIN)
    try:
        return governance_service.update_team(team_id, payload, principal)
    except StopIteration:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found") from None


@router.post("/org/team-memberships", response_model=TeamRecord, status_code=status.HTTP_200_OK)
def add_org_team_membership(
    payload: AddTeamMembershipRequest,
    principal: Annotated[Principal, Depends(get_principal)],
) -> TeamRecord:
    ensure_roles(principal, PrincipalRole.ADMIN)
    try:
        return governance_service.add_team_membership(payload, principal)
    except StopIteration:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team or user not found") from None


@router.get("/org/portfolios", response_model=list[PortfolioRecord])
def list_org_portfolios(principal: Annotated[Principal, Depends(get_principal)]) -> list[PortfolioRecord]:
    ensure_roles(principal, PrincipalRole.ADMIN)
    return governance_service.list_portfolios(principal)


@router.post("/org/portfolios", response_model=PortfolioRecord, status_code=status.HTTP_201_CREATED)
def create_org_portfolio(
    payload: CreatePortfolioRequest,
    principal: Annotated[Principal, Depends(get_principal)],
) -> PortfolioRecord:
    ensure_roles(principal, PrincipalRole.ADMIN)
    try:
        return governance_service.create_portfolio(payload, principal)
    except StopIteration:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Owner team not found") from None
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
