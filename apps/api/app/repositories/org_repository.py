"""Organization repository — owns tenant, user, organization, team, and portfolio CRUD.

Delegates to governance_repository for now; the actual method implementations
will be migrated here incrementally as the monolith is decomposed.
"""

from __future__ import annotations

from app.models.governance import (
    AddTeamMembershipRequest,
    CreateOrganizationRequest,
    CreatePortfolioRequest,
    CreateTenantRequest,
    CreateTeamRequest,
    CreateUserRequest,
    IntegrationRecord,
    CreateIntegrationRequest,
    OrganizationRecord,
    PolicyRecord,
    PolicyRuleUpdateRequest,
    PortfolioRecord,
    PortfolioSummary,
    TeamRecord,
    TenantRecord,
    UpdateIntegrationRequest,
    UpdateOrganizationRequest,
    UpdateTenantRequest,
    UpdateTeamRequest,
    UpdateUserRequest,
    UserRecord,
)
from app.models.security import Principal
from app.repositories.governance_repository import governance_repository


class OrgRepository:
    """Encapsulates all organizational hierarchy and identity operations."""

    # -- Tenants --
    def list_tenants(self) -> list[TenantRecord]:
        return governance_repository.list_tenants()

    def create_tenant(self, payload: CreateTenantRequest) -> TenantRecord:
        return governance_repository.create_tenant(payload)

    def update_tenant(self, tenant_id: str, payload: UpdateTenantRequest) -> TenantRecord:
        return governance_repository.update_tenant(tenant_id, payload)

    # -- Users --
    def list_users(self, tenant_id: str | None = None) -> list[UserRecord]:
        return governance_repository.list_users(tenant_id)

    def create_user(self, payload: CreateUserRequest, tenant_id: str) -> UserRecord:
        return governance_repository.create_user(payload, tenant_id)

    def update_user(self, user_id: str, payload: UpdateUserRequest, tenant_id: str) -> UserRecord:
        return governance_repository.update_user(user_id, payload, tenant_id)

    def authenticate_local_user(self, email: str, password: str, tenant_id: str | None = None) -> Principal:
        return governance_repository.authenticate_local_user(email, password, tenant_id)

    # -- Organizations --
    def list_organizations(self, tenant_id: str | None = None) -> list[OrganizationRecord]:
        return governance_repository.list_organizations(tenant_id)

    def create_organization(self, payload: CreateOrganizationRequest, tenant_id: str) -> OrganizationRecord:
        return governance_repository.create_organization(payload, tenant_id)

    def update_organization(self, organization_id: str, payload: UpdateOrganizationRequest, tenant_id: str) -> OrganizationRecord:
        return governance_repository.update_organization(organization_id, payload, tenant_id)

    # -- Teams --
    def list_teams(self, tenant_id: str | None = None) -> list[TeamRecord]:
        return governance_repository.list_teams(tenant_id)

    def create_team(self, payload: CreateTeamRequest, tenant_id: str) -> TeamRecord:
        return governance_repository.create_team(payload, tenant_id)

    def update_team(self, team_id: str, payload: UpdateTeamRequest, tenant_id: str) -> TeamRecord:
        return governance_repository.update_team(team_id, payload, tenant_id)

    def add_team_membership(self, payload: AddTeamMembershipRequest, tenant_id: str) -> TeamRecord:
        return governance_repository.add_team_membership(payload, tenant_id)

    # -- Portfolios --
    def list_portfolios(self, tenant_id: str | None = None) -> list[PortfolioRecord]:
        return governance_repository.list_portfolios(tenant_id)

    def create_portfolio(self, payload: CreatePortfolioRequest, tenant_id: str) -> PortfolioRecord:
        return governance_repository.create_portfolio(payload, tenant_id)

    def list_portfolio_summaries(self, tenant_id: str | None = None) -> list[PortfolioSummary]:
        return governance_repository.list_portfolio_summaries(tenant_id)

    # -- Integrations --
    def list_integrations(self, tenant_id: str | None = None) -> list[IntegrationRecord]:
        return governance_repository.list_integrations(tenant_id)

    def create_integration(self, payload: CreateIntegrationRequest, tenant_id: str) -> IntegrationRecord:
        return governance_repository.create_integration(payload, tenant_id)

    def update_integration(self, integration_id: str, payload: UpdateIntegrationRequest, tenant_id: str) -> IntegrationRecord:
        return governance_repository.update_integration(integration_id, payload, tenant_id)

    def delete_integration(self, integration_id: str, tenant_id: str) -> None:
        governance_repository.delete_integration(integration_id, tenant_id)

    # -- Policies --
    def list_policies(self, tenant_id: str | None = None) -> list[PolicyRecord]:
        return governance_repository.list_policies(tenant_id)

    def update_policy_rules(self, policy_id: str, payload: PolicyRuleUpdateRequest, tenant_id: str) -> PolicyRecord:
        return governance_repository.update_policy_rules(policy_id, payload, tenant_id)


org_repository = OrgRepository()
