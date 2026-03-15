"""FastAPI application factory."""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from starlette.requests import Request

from app.config import get_settings
from app.interface.api.middleware import ObservabilityMiddleware, RequestIDMiddleware
from app.interface.api.routes import router
from app.infrastructure.metrics import get_metrics

settings = get_settings()

# Structured logging (JSON) for production-style observability
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("github_doctor")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=settings.api_title,
        version=settings.api_version,
        description="Analyze GitHub repositories and generate health reports.",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(ObservabilityMiddleware)
    app.add_middleware(RequestIDMiddleware)

    @app.get("/")
    def root() -> dict:
        return {
            "service": settings.api_title,
            "version": settings.api_version,
            "docs": "/docs",
            "health": "/health",
            "metrics": "/metrics",
            "analyze": "/analyze/{owner}/{repo}",
        }

    @app.get("/health")
    def health() -> dict:
        """Health check for load balancers and orchestrators (e.g. Kubernetes)."""
        return {"status": "ok", "version": settings.api_version}

    @app.get("/metrics")
    async def metrics(request: Request) -> dict | PlainTextResponse:
        """
        Application metrics. Returns JSON by default.
        Use Accept: text/plain for Prometheus exposition format.
        """
        accept = request.headers.get("Accept", "")
        if "text/plain" in accept or "application/openmetrics" in accept:
            return PlainTextResponse(get_metrics().prometheus(), media_type="text/plain")
        return get_metrics().snapshot()

    app.include_router(router)
    return app


app = create_app()
