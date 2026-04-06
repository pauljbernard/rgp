from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.models.common import PaginatedResponse
from app.core.auth import get_principal
from app.models.governance import AnalyticsAgentRow, AnalyticsBottleneckRow, AnalyticsWorkflowRow, AuditEntry, DeliveryDoraRow, DeliveryForecastPoint, DeliveryForecastSummary, DeliveryLifecycleRow, DeliveryTrendPoint, PerformanceMetricRecord, PerformanceOperationsSummary, PerformanceOperationsTrendPoint, PerformanceRouteSummary, PerformanceSloSummary, PerformanceTrendPoint
from app.models.governance import AgentTrendPoint, WorkflowTrendPoint
from app.models.security import Principal
from app.services.governance_service import governance_service

router = APIRouter()


@router.get("/workflows", response_model=list[AnalyticsWorkflowRow])
def list_workflow_analytics(
    days: int = Query(default=30, ge=1, le=365),
    team_id: str | None = Query(default=None),
    user_id: str | None = Query(default=None),
    portfolio_id: str | None = Query(default=None),
    principal: Annotated[Principal, Depends(get_principal)] = None,
) -> list[AnalyticsWorkflowRow]:
    return governance_service.list_workflow_analytics(days, principal.tenant_id, team_id, user_id, portfolio_id)


@router.get("/workflows/trends", response_model=list[WorkflowTrendPoint])
def list_workflow_trends(
    days: int = Query(default=30, ge=1, le=365),
    team_id: str | None = Query(default=None),
    user_id: str | None = Query(default=None),
    portfolio_id: str | None = Query(default=None),
    workflow: str | None = Query(default=None),
    principal: Annotated[Principal, Depends(get_principal)] = None,
) -> list[WorkflowTrendPoint]:
    return governance_service.list_workflow_trends(days, principal.tenant_id, team_id, user_id, portfolio_id, workflow)


@router.get("/workflows/{workflow}/history", response_model=list[AuditEntry])
def get_workflow_history(
    workflow: str,
    limit: int = Query(default=200, ge=1, le=500),
    principal: Annotated[Principal, Depends(get_principal)] = None,
) -> list[AuditEntry]:
    return governance_service.get_workflow_history(workflow, principal, limit)


@router.get("/agents", response_model=list[AnalyticsAgentRow])
def list_agent_analytics(
    days: int = Query(default=30, ge=1, le=365),
    team_id: str | None = Query(default=None),
    user_id: str | None = Query(default=None),
    portfolio_id: str | None = Query(default=None),
    principal: Annotated[Principal, Depends(get_principal)] = None,
) -> list[AnalyticsAgentRow]:
    return governance_service.list_agent_analytics(days, principal.tenant_id, team_id, user_id, portfolio_id)


@router.get("/agents/trends", response_model=list[AgentTrendPoint])
def list_agent_trends(
    days: int = Query(default=30, ge=1, le=365),
    team_id: str | None = Query(default=None),
    user_id: str | None = Query(default=None),
    portfolio_id: str | None = Query(default=None),
    agent: str | None = Query(default=None),
    principal: Annotated[Principal, Depends(get_principal)] = None,
) -> list[AgentTrendPoint]:
    return governance_service.list_agent_trends(days, principal.tenant_id, team_id, user_id, portfolio_id, agent)


@router.get("/bottlenecks", response_model=list[AnalyticsBottleneckRow])
def list_bottleneck_analytics(
    days: int = Query(default=30, ge=1, le=365),
    principal: Annotated[Principal, Depends(get_principal)] = None,
) -> list[AnalyticsBottleneckRow]:
    return governance_service.list_bottleneck_analytics(days, principal.tenant_id)


@router.get("/performance/routes", response_model=PaginatedResponse[PerformanceRouteSummary])
def list_performance_route_summaries(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    days: int = Query(default=30, ge=1, le=365),
    principal: Annotated[Principal, Depends(get_principal)] = None,
) -> PaginatedResponse[PerformanceRouteSummary]:
    return governance_service.list_performance_route_summaries(page, page_size, days, principal)


@router.get("/performance/slo", response_model=PaginatedResponse[PerformanceSloSummary])
def list_performance_slo_summaries(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    days: int = Query(default=30, ge=1, le=365),
    principal: Annotated[Principal, Depends(get_principal)] = None,
) -> PaginatedResponse[PerformanceSloSummary]:
    return governance_service.list_performance_slo_summaries(page, page_size, days, principal)


@router.get("/performance/metrics", response_model=PaginatedResponse[PerformanceMetricRecord])
def list_performance_metrics(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    days: int = Query(default=30, ge=1, le=365),
    route: str | None = Query(default=None),
    method: str | None = Query(default=None),
    status_code: int | None = Query(default=None, ge=100, le=599),
    principal: Annotated[Principal, Depends(get_principal)] = None,
) -> PaginatedResponse[PerformanceMetricRecord]:
    return governance_service.list_performance_metrics(page, page_size, days, principal, route, method, status_code)


@router.get("/performance/trends", response_model=PaginatedResponse[PerformanceTrendPoint])
def list_performance_trends(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    days: int = Query(default=30, ge=1, le=365),
    route: str | None = Query(default=None),
    method: str | None = Query(default=None),
    principal: Annotated[Principal, Depends(get_principal)] = None,
) -> PaginatedResponse[PerformanceTrendPoint]:
    return governance_service.list_performance_trends(page, page_size, days, principal, route, method)


@router.get("/performance/operations", response_model=PerformanceOperationsSummary)
def get_performance_operations_summary(
    principal: Annotated[Principal, Depends(get_principal)] = None,
) -> PerformanceOperationsSummary:
    return governance_service.get_performance_operations_summary(principal)


@router.get("/performance/operations/trends", response_model=list[PerformanceOperationsTrendPoint])
def list_performance_operations_trends(
    days: int = Query(default=30, ge=1, le=365),
    principal: Annotated[Principal, Depends(get_principal)] = None,
) -> list[PerformanceOperationsTrendPoint]:
    return governance_service.list_performance_operations_trends(principal, days)


@router.get("/delivery/dora", response_model=list[DeliveryDoraRow])
def list_delivery_dora(
    portfolio_id: str | None = Query(default=None),
    team_id: str | None = Query(default=None),
    user_id: str | None = Query(default=None),
    principal: Annotated[Principal, Depends(get_principal)] = None,
) -> list[DeliveryDoraRow]:
    return governance_service.list_delivery_dora(principal, portfolio_id, team_id, user_id)


@router.get("/delivery/lifecycle", response_model=list[DeliveryLifecycleRow])
def list_delivery_lifecycle(
    portfolio_id: str | None = Query(default=None),
    team_id: str | None = Query(default=None),
    user_id: str | None = Query(default=None),
    principal: Annotated[Principal, Depends(get_principal)] = None,
) -> list[DeliveryLifecycleRow]:
    return governance_service.list_delivery_lifecycle(principal, portfolio_id, team_id, user_id)


@router.get("/delivery/trends", response_model=list[DeliveryTrendPoint])
def list_delivery_trends(
    days: int = Query(default=30, ge=1, le=365),
    portfolio_id: str | None = Query(default=None),
    team_id: str | None = Query(default=None),
    user_id: str | None = Query(default=None),
    principal: Annotated[Principal, Depends(get_principal)] = None,
) -> list[DeliveryTrendPoint]:
    return governance_service.list_delivery_trends(principal, days, portfolio_id, team_id, user_id)


@router.get("/delivery/forecast", response_model=DeliveryForecastSummary)
def get_delivery_forecast(
    history_days: int = Query(default=30, ge=7, le=365),
    forecast_days: int = Query(default=14, ge=1, le=90),
    portfolio_id: str | None = Query(default=None),
    team_id: str | None = Query(default=None),
    user_id: str | None = Query(default=None),
    principal: Annotated[Principal, Depends(get_principal)] = None,
) -> DeliveryForecastSummary:
    return governance_service.get_delivery_forecast(principal, history_days, forecast_days, portfolio_id, team_id, user_id)


@router.get("/delivery/forecast/trends", response_model=list[DeliveryForecastPoint])
def list_delivery_forecast_points(
    history_days: int = Query(default=30, ge=7, le=365),
    forecast_days: int = Query(default=14, ge=1, le=90),
    portfolio_id: str | None = Query(default=None),
    team_id: str | None = Query(default=None),
    user_id: str | None = Query(default=None),
    principal: Annotated[Principal, Depends(get_principal)] = None,
) -> list[DeliveryForecastPoint]:
    return governance_service.list_delivery_forecast_points(principal, history_days, forecast_days, portfolio_id, team_id, user_id)
