from collections.abc import Awaitable, Callable
from typing import Any

from fastapi import FastAPI

from app.api.v1.router import api_router


def create_app(
    *,
    openapi_url: str | None = None,
    docs_url: str | None = None,
    lifespan: Callable[[FastAPI], Awaitable[Any]] | None = None,
) -> FastAPI:
    app = FastAPI(
        title="Request Governance Platform API",
        version="0.1.0",
        openapi_url=openapi_url,
        docs_url=docs_url,
        lifespan=lifespan,
    )

    app.include_router(api_router, prefix="/api/v1")

    return app
