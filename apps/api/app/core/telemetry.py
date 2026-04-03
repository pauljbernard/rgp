from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

from app.core.config import settings
from app.db.session import engine


def configure_telemetry(app) -> None:
    if not settings.telemetry_enabled:
        return

    resource = Resource.create(
        {
            "service.name": settings.telemetry_service_name,
            "deployment.environment": settings.app_env,
        }
    )
    provider = TracerProvider(resource=resource)
    provider.add_span_processor(BatchSpanProcessor(_trace_exporter()))
    trace.set_tracer_provider(provider)

    FastAPIInstrumentor.instrument_app(app, tracer_provider=provider)
    SQLAlchemyInstrumentor().instrument(engine=engine, tracer_provider=provider)


def current_trace_ids() -> tuple[str | None, str | None]:
    span = trace.get_current_span()
    context = span.get_span_context()
    if not context or not context.is_valid:
        return None, None
    return f"{context.trace_id:032x}", f"{context.span_id:016x}"


def _trace_exporter():
    if settings.telemetry_exporter == "otlp" and settings.telemetry_otlp_endpoint:
        return OTLPSpanExporter(endpoint=settings.telemetry_otlp_endpoint)
    return ConsoleSpanExporter()
