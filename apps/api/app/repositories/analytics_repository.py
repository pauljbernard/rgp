"""Analytics repository — owns all workflow, agent, delivery, and performance analytics.

Delegates to governance_repository for now; the actual method implementations
will be migrated here incrementally as the monolith is decomposed.
"""

from __future__ import annotations

from app.models.governance import (
    AnalyticsAgentRow,
    AnalyticsBottleneckRow,
    AnalyticsWorkflowRow,
    AgentTrendPoint,
    DeliveryDoraRow,
    DeliveryForecastPoint,
    DeliveryForecastSummary,
    DeliveryLifecycleRow,
    DeliveryTrendPoint,
    PerformanceOperationsSummary,
    PerformanceOperationsTrendPoint,
    WorkflowTrendPoint,
)
from app.repositories.governance_repository import governance_repository


class AnalyticsRepository:
    """Encapsulates all analytics and reporting queries."""

    def list_workflow_analytics(
        self, days: int = 30, tenant_id: str | None = None,
        team_id: str | None = None, user_id: str | None = None,
        portfolio_id: str | None = None,
    ) -> list[AnalyticsWorkflowRow]:
        return governance_repository.list_workflow_analytics(days, tenant_id, team_id, user_id, portfolio_id)

    def list_workflow_trends(
        self, days: int = 30, tenant_id: str | None = None,
        team_id: str | None = None, user_id: str | None = None,
        portfolio_id: str | None = None, workflow: str | None = None,
    ) -> list[WorkflowTrendPoint]:
        return governance_repository.list_workflow_trends(days, tenant_id, team_id, user_id, portfolio_id, workflow)

    def list_agent_analytics(
        self, days: int = 30, tenant_id: str | None = None,
        team_id: str | None = None, user_id: str | None = None,
        portfolio_id: str | None = None,
    ) -> list[AnalyticsAgentRow]:
        return governance_repository.list_agent_analytics(days, tenant_id, team_id, user_id, portfolio_id)

    def list_agent_trends(
        self, days: int = 30, tenant_id: str | None = None,
        team_id: str | None = None, user_id: str | None = None,
        portfolio_id: str | None = None, agent: str | None = None,
    ) -> list[AgentTrendPoint]:
        return governance_repository.list_agent_trends(days, tenant_id, team_id, user_id, portfolio_id, agent)

    def list_bottleneck_analytics(self, days: int = 30, tenant_id: str | None = None) -> list[AnalyticsBottleneckRow]:
        return governance_repository.list_bottleneck_analytics(days, tenant_id)

    def list_delivery_dora(
        self, tenant_id: str | None = None, portfolio_id: str | None = None,
        team_id: str | None = None, user_id: str | None = None,
    ) -> list[DeliveryDoraRow]:
        return governance_repository.list_delivery_dora(tenant_id, portfolio_id, team_id, user_id)

    def list_delivery_lifecycle(
        self, tenant_id: str | None = None, portfolio_id: str | None = None,
        team_id: str | None = None, user_id: str | None = None,
    ) -> list[DeliveryLifecycleRow]:
        return governance_repository.list_delivery_lifecycle(tenant_id, portfolio_id, team_id, user_id)

    def list_delivery_trends(
        self, tenant_id: str | None = None, days: int = 30,
        portfolio_id: str | None = None, team_id: str | None = None,
        user_id: str | None = None,
    ) -> list[DeliveryTrendPoint]:
        return governance_repository.list_delivery_trends(tenant_id, days, portfolio_id, team_id, user_id)

    def get_delivery_forecast(
        self, tenant_id: str | None = None, history_days: int = 30,
        forecast_days: int = 14, portfolio_id: str | None = None,
        team_id: str | None = None, user_id: str | None = None,
    ) -> DeliveryForecastSummary:
        return governance_repository.get_delivery_forecast(tenant_id, history_days, forecast_days, portfolio_id, team_id, user_id)

    def list_delivery_forecast_points(
        self, tenant_id: str | None = None, history_days: int = 30,
        forecast_days: int = 14, portfolio_id: str | None = None,
        team_id: str | None = None, user_id: str | None = None,
    ) -> list[DeliveryForecastPoint]:
        return governance_repository.list_delivery_forecast_points(tenant_id, history_days, forecast_days, portfolio_id, team_id, user_id)

    def get_performance_operations_summary(self, tenant_id: str | None = None) -> PerformanceOperationsSummary:
        return governance_repository.get_performance_operations_summary(tenant_id)

    def list_performance_operations_trends(self, tenant_id: str | None = None, days: int = 30) -> list[PerformanceOperationsTrendPoint]:
        return governance_repository.list_performance_operations_trends(tenant_id, days)


analytics_repository = AnalyticsRepository()
