"""Middleware: request ID, structured logging, metrics timing."""

import json
import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from back.infrastructure.metrics import get_metrics

logger = logging.getLogger("github_doctor")


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Add X-Request-ID to request and response. Use for tracing."""

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


class ObservabilityMiddleware(BaseHTTPMiddleware):
    """Log request/response (structured JSON) and record request duration in metrics."""

    async def dispatch(self, request: Request, call_next):
        metrics = get_metrics()
        metrics.record_request_start()
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = metrics.record_request_end()
        request_id = getattr(request.state, "request_id", None)
        log_payload = {
            "event": "request",
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": round(duration_ms, 2),
        }
        logger.info(json.dumps(log_payload))
        return response
