import time
import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging import logger
from app.core.metrics import (
    http_request_duration_seconds,
    http_requests_total,
)
from app.core.request_context import set_request_id


class RequestLoggingMiddleware(BaseHTTPMiddleware):

    async def dispatch(
        self,
        request: Request,
        call_next,
    ):
        start_time = time.perf_counter()
        endpoint = request.url.path
        method = request.method

        request_id = request.headers.get(
            "X-Request-ID",
            str(uuid.uuid4()),
        )

        set_request_id(request_id)

        try:
            response = await call_next(request)

        except Exception as e:
            duration_seconds = time.perf_counter() - start_time
            duration_ms = duration_seconds * 1000

            http_requests_total.labels(
                method=method,
                endpoint=endpoint,
                status="500",
            ).inc()

            http_request_duration_seconds.labels(
                method=method,
                endpoint=endpoint,
            ).observe(duration_seconds)

            logger.error(
                "%s %s | request_id=%s | failed after %.2fms: %s",
                method,
                endpoint,
                request_id,
                duration_ms,
                e,
            )

            raise

        duration_seconds = time.perf_counter() - start_time
        duration_ms = duration_seconds * 1000

        status_code = str(response.status_code)

        response.headers["X-Request-ID"] = request_id

        http_requests_total.labels(
            method=method,
            endpoint=endpoint,
            status=status_code,
        ).inc()

        http_request_duration_seconds.labels(
            method=method,
            endpoint=endpoint,
        ).observe(duration_seconds)

        logger.info(
            "%s %s | %s | %.2fms | request_id=%s",
            method,
            endpoint,
            status_code,
            duration_ms,
            request_id,
        )

        return response