from datetime import datetime, timedelta, timezone

from app.core.config import settings
from app.db.models import PerformanceMetricTable
from app.db.session import SessionLocal
from app.models.common import PaginatedResponse
from app.models.governance import PerformanceMetricRecord, PerformanceRouteSummary, PerformanceSloSummary, PerformanceTrendPoint


class PerformanceMetricsService:
    def record_api_request(
        self,
        *,
        tenant_id: str,
        route: str,
        method: str,
        status_code: int,
        duration_ms: float,
        trace_id: str | None,
        span_id: str | None,
        correlation_id: str | None,
    ) -> None:
        with SessionLocal() as session:
            session.add(
                PerformanceMetricTable(
                    tenant_id=tenant_id,
                    metric_type="api_request",
                    route=route,
                    method=method,
                    status_code=status_code,
                    duration_ms=round(duration_ms, 2),
                    trace_id=trace_id,
                    span_id=span_id,
                    correlation_id=correlation_id,
                    occurred_at=datetime.now(timezone.utc),
                )
            )
            session.commit()

    def list_route_summaries(self, *, tenant_id: str, days: int, page: int, page_size: int) -> PaginatedResponse[PerformanceRouteSummary]:
        rows = self._load_api_rows(tenant_id=tenant_id, days=days)
        grouped: dict[tuple[str, str], list[PerformanceMetricTable]] = {}
        for row in rows:
            grouped.setdefault((row.route, row.method), []).append(row)

        summaries: list[PerformanceRouteSummary] = []
        for (route, method), metric_rows in grouped.items():
            durations = sorted(row.duration_ms for row in metric_rows)
            total = len(metric_rows)
            errors = sum(1 for row in metric_rows if row.status_code >= 500)
            satisfied = sum(1 for row in metric_rows if row.duration_ms <= settings.performance_latency_slo_ms)
            p95_index = min(total - 1, max(0, int(total * 0.95) - 1))
            summaries.append(
                PerformanceRouteSummary(
                    route=route,
                    method=method,
                    request_count=total,
                    error_rate=f"{(errors / total) * 100:.1f}%",
                    avg_duration_ms=round(sum(durations) / total, 2),
                    p95_duration_ms=round(durations[p95_index], 2),
                    apdex=f"{(satisfied / total):.2f}",
                )
            )
        summaries.sort(key=lambda row: (-row.request_count, row.route, row.method))
        return self._paginate(summaries, page, page_size)

    def list_slo_summaries(self, *, tenant_id: str, days: int, page: int, page_size: int) -> PaginatedResponse[PerformanceSloSummary]:
        rows = self._load_api_rows(tenant_id=tenant_id, days=days)
        grouped: dict[tuple[str, str], list[PerformanceMetricTable]] = {}
        for row in rows:
            grouped.setdefault((row.route, row.method), []).append(row)

        summaries: list[PerformanceSloSummary] = []
        for (route, method), metric_rows in grouped.items():
            durations = sorted(row.duration_ms for row in metric_rows)
            total = len(metric_rows)
            errors = sum(1 for row in metric_rows if row.status_code >= 500)
            availability = ((total - errors) / total) * 100
            p95_index = min(total - 1, max(0, int(total * 0.95) - 1))
            p95_duration = durations[p95_index]
            status = "healthy"
            if availability < settings.performance_availability_slo_percent or p95_duration > settings.performance_latency_slo_ms:
                status = "at_risk"
            if availability < settings.performance_availability_slo_percent - 2 or p95_duration > settings.performance_latency_slo_ms * 1.5:
                status = "breached"
            error_budget_remaining = max(0.0, availability - (100 - (100 - settings.performance_availability_slo_percent)))
            summaries.append(
                PerformanceSloSummary(
                    route=route,
                    method=method,
                    availability_slo=f"{settings.performance_availability_slo_percent:.1f}%",
                    latency_slo_ms=settings.performance_latency_slo_ms,
                    availability_actual=f"{availability:.2f}%",
                    p95_duration_ms=round(p95_duration, 2),
                    status=status,
                    error_budget_remaining=f"{max(0.0, availability - (100 - (100 - settings.performance_availability_slo_percent))):.2f}%",
                )
            )
        summaries.sort(key=lambda row: (row.status != "breached", row.status != "at_risk", row.route, row.method))
        return self._paginate(summaries, page, page_size)

    def list_raw_metrics(
        self,
        *,
        tenant_id: str,
        days: int,
        page: int,
        page_size: int,
        route: str | None = None,
        method: str | None = None,
        status_code: int | None = None,
    ) -> PaginatedResponse[PerformanceMetricRecord]:
        rows = self._load_api_rows(tenant_id=tenant_id, days=days)
        if route:
            rows = [row for row in rows if row.route == route]
        if method:
            rows = [row for row in rows if row.method == method.upper()]
        if status_code is not None:
            rows = [row for row in rows if row.status_code == status_code]
        rows.sort(key=lambda row: (row.occurred_at, row.id), reverse=True)
        records = [
            PerformanceMetricRecord(
                id=row.id,
                route=row.route,
                method=row.method,
                status_code=row.status_code,
                duration_ms=row.duration_ms,
                trace_id=row.trace_id,
                span_id=row.span_id,
                correlation_id=row.correlation_id,
                occurred_at=row.occurred_at.isoformat().replace("+00:00", "Z"),
            )
            for row in rows
        ]
        return self._paginate(records, page, page_size)

    def list_route_trends(
        self,
        *,
        tenant_id: str,
        days: int,
        page: int,
        page_size: int,
        route: str | None = None,
        method: str | None = None,
    ) -> PaginatedResponse[PerformanceTrendPoint]:
        rows = self._load_api_rows(tenant_id=tenant_id, days=days)
        if route:
            rows = [row for row in rows if row.route == route]
        if method:
            rows = [row for row in rows if row.method == method.upper()]
        grouped: dict[tuple[str, str, str], list[PerformanceMetricTable]] = {}
        for row in rows:
            period_start = row.occurred_at.astimezone(timezone.utc).strftime("%Y-%m-%d")
            grouped.setdefault((period_start, row.route, row.method), []).append(row)

        trends: list[PerformanceTrendPoint] = []
        for (period_start, grouped_route, grouped_method), metric_rows in grouped.items():
            durations = sorted(row.duration_ms for row in metric_rows)
            total = len(metric_rows)
            errors = sum(1 for row in metric_rows if row.status_code >= 500)
            p95_index = min(total - 1, max(0, int(total * 0.95) - 1))
            trends.append(
                PerformanceTrendPoint(
                    period_start=period_start,
                    route=grouped_route,
                    method=grouped_method,
                    request_count=total,
                    avg_duration_ms=round(sum(durations) / total, 2),
                    p95_duration_ms=round(durations[p95_index], 2),
                    error_rate=f"{(errors / total) * 100:.1f}%",
                )
            )
        trends.sort(key=lambda row: (row.period_start, row.route, row.method), reverse=True)
        return self._paginate(trends, page, page_size)

    def _load_api_rows(self, *, tenant_id: str, days: int) -> list[PerformanceMetricTable]:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        with SessionLocal() as session:
            return (
                session.query(PerformanceMetricTable)
                .filter(
                    PerformanceMetricTable.tenant_id == tenant_id,
                    PerformanceMetricTable.metric_type == "api_request",
                    PerformanceMetricTable.occurred_at >= cutoff,
                )
                .all()
            )

    def _paginate(self, items, page: int, page_size: int):
        total_count = len(items)
        total_pages = max(1, (total_count + page_size - 1) // page_size)
        current_page = min(max(page, 1), total_pages)
        start = (current_page - 1) * page_size
        end = start + page_size
        return PaginatedResponse(
            items=items[start:end],
            page=current_page,
            page_size=page_size,
            total_count=total_count,
            total_pages=total_pages,
        )


performance_metrics_service = PerformanceMetricsService()
