from __future__ import annotations

import logging
from time import perf_counter
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse

from app.factory import create_app
from app.core.auth import try_get_request_principal
from app.core.config import settings
from app.core.telemetry import current_trace_ids, trace
from app.models.common import ErrorDetail, ErrorEnvelope
from app.runtime_bootstrap import ensure_runtime_bootstrapped, runtime_lifespan
from app.services.performance_metrics_service import performance_metrics_service

_app: FastAPI | None = None
_lambda_handler = None
logger = logging.getLogger(__name__)


def get_asgi_app() -> FastAPI:
    global _app

    if _app is None:
        _app = create_app(
            openapi_url="/openapi.json",
            docs_url="/docs",
            lifespan=runtime_lifespan(),
        )
        _configure_http_runtime(_app)
        _register_http_shell(_app)
    return _app


def build_lambda_handler():
    try:
        from mangum import Mangum
    except ImportError as exc:
        raise RuntimeError(
            "Mangum is required for Lambda execution. Install rgp-api with the 'aws' optional dependency."
        ) from exc
    app = get_asgi_app()
    ensure_runtime_bootstrapped(app)
    return Mangum(app, lifespan="off")


def get_lambda_handler():
    global _lambda_handler

    if _lambda_handler is None:
        _lambda_handler = build_lambda_handler()
    return _lambda_handler


def lambda_handler(event, context):
    return get_lambda_handler()(event, context)


def _register_http_shell(app: FastAPI) -> None:
    @app.get("/healthz")
    def healthcheck() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/docs", include_in_schema=False)
    def legacy_docs_redirect() -> RedirectResponse:
        return RedirectResponse(url="/docs", status_code=status.HTTP_307_TEMPORARY_REDIRECT)

    @app.get("/api/openapi.json", include_in_schema=False)
    def legacy_openapi_redirect() -> RedirectResponse:
        return RedirectResponse(url="/openapi.json", status_code=status.HTTP_307_TEMPORARY_REDIRECT)


def _configure_http_runtime(app: FastAPI) -> None:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    def _correlation_id(request: Request) -> str:
        existing = getattr(request.state, "correlation_id", None)
        if existing:
            return existing
        generated = f"corr_{uuid4().hex}"
        request.state.correlation_id = generated
        return generated

    def _error_response(
        request: Request,
        *,
        status_code: int,
        code: str,
        message: str,
        details: list[ErrorDetail] | None = None,
        retryable: bool = False,
    ) -> JSONResponse:
        correlation_id = _correlation_id(request)
        payload = ErrorEnvelope(
            error={
                "code": code,
                "message": message,
                "details": details or [],
                "correlation_id": correlation_id,
                "retryable": retryable,
            }
        )
        return JSONResponse(
            status_code=status_code,
            content=payload.model_dump(mode="json"),
            headers={"X-Correlation-Id": correlation_id},
        )

    @app.middleware("http")
    async def attach_correlation_id(request: Request, call_next):
        request.state.correlation_id = f"corr_{uuid4().hex}"
        start = perf_counter()
        tracer = trace.get_tracer("rgp.api.http")
        with tracer.start_as_current_span(f"{request.method} {request.url.path}") as span:
            span.set_attribute("http.request.method", request.method)
            span.set_attribute("url.path", request.url.path)
            span.set_attribute("rgp.correlation_id", request.state.correlation_id)
            response = await call_next(request)
            response.headers["X-Correlation-Id"] = request.state.correlation_id
            trace_id, span_id = current_trace_ids()
            if trace_id and span_id:
                response.headers["X-Trace-Id"] = trace_id
                response.headers["X-Span-Id"] = span_id
            try:
                principal = try_get_request_principal(request)
                route = getattr(request.scope.get("route"), "path", request.url.path)
                performance_metrics_service.record_api_request(
                    tenant_id=principal.tenant_id if principal else "system",
                    route=route,
                    method=request.method,
                    status_code=response.status_code,
                    duration_ms=(perf_counter() - start) * 1000,
                    trace_id=trace_id,
                    span_id=span_id,
                    correlation_id=request.state.correlation_id,
                )
            except Exception as exc:
                logger.debug("Performance metric recording failed: %s", exc)
            return response

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        detail = exc.detail
        if isinstance(detail, dict) and "error" in detail:
            correlation_id = _correlation_id(request)
            return JSONResponse(
                status_code=exc.status_code,
                content=detail,
                headers={"X-Correlation-Id": correlation_id},
            )
        message = detail if isinstance(detail, str) else "Request failed."
        code_map = {
            status.HTTP_400_BAD_REQUEST: "BAD_REQUEST",
            status.HTTP_401_UNAUTHORIZED: "UNAUTHORIZED",
            status.HTTP_403_FORBIDDEN: "FORBIDDEN",
            status.HTTP_404_NOT_FOUND: "NOT_FOUND",
            status.HTTP_409_CONFLICT: "CONFLICT",
            status.HTTP_422_UNPROCESSABLE_ENTITY: "VALIDATION_ERROR",
        }
        return _error_response(
            request,
            status_code=exc.status_code,
            code=code_map.get(exc.status_code, "HTTP_ERROR"),
            message=message,
            retryable=exc.status_code >= 500,
        )

    @app.exception_handler(RequestValidationError)
    async def request_validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        details = [
            ErrorDetail(field=".".join(str(part) for part in error["loc"][1:]) or None, message=error["msg"])
            for error in exc.errors()
        ]
        return _error_response(
            request,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="REQUEST_VALIDATION_FAILED",
            message="Request payload failed validation.",
            details=details,
            retryable=False,
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        return _error_response(
            request,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="INTERNAL_SERVER_ERROR",
            message="An unexpected error occurred.",
            details=[ErrorDetail(message=str(exc))] if settings.app_env.lower() == "development" else [],
            retryable=False,
        )
