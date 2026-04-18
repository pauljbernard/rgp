from __future__ import annotations

from collections.abc import Awaitable, Callable
from contextlib import asynccontextmanager
from threading import Lock
from typing import Any

from fastapi import FastAPI

from app.core.config import settings
from app.core.telemetry import configure_telemetry
from app.db.bootstrap import initialize_database
from app.persistence.dynamodb_bootstrap import initialize_request_slice, initialize_template_slice

_bootstrap_lock = Lock()
_database_initialized = False
_template_slice_initialized = False
_request_slice_initialized = False
_telemetry_instrumented_apps: set[int] = set()


def ensure_runtime_bootstrapped(app: FastAPI | None = None) -> None:
    global _database_initialized, _template_slice_initialized, _request_slice_initialized

    with _bootstrap_lock:
        if app is not None:
            app_id = id(app)
            if app_id not in _telemetry_instrumented_apps:
                configure_telemetry(app)
                _telemetry_instrumented_apps.add(app_id)

        if not _database_initialized:
            initialize_database()
            _database_initialized = True

        if _template_backend() == "dynamodb" and not _template_slice_initialized:
            initialize_template_slice()
            _template_slice_initialized = True

        if _request_backend() == "dynamodb" and not _request_slice_initialized:
            initialize_request_slice()
            _request_slice_initialized = True


def runtime_lifespan() -> Callable[[FastAPI], Awaitable[Any]]:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        ensure_runtime_bootstrapped(app)
        yield

    return lifespan


def _template_backend() -> str:
    return (settings.template_persistence_backend or settings.persistence_backend or "sqlalchemy").lower()


def _request_backend() -> str:
    return (settings.request_persistence_backend or settings.persistence_backend or "sqlalchemy").lower()
