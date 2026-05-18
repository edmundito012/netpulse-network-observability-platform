import time

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging import logger
from app.core.metrics import (
    http_request_duration_seconds,
    http_requests_total,
)


class RequestLoggingMiddleware(BaseHTTPMiddleware):

    async def dispatch(
        self,
        request: Request,
        call_next,
    ):
        start_time = time.perf_counter()
        endpoint = request.url.path
        method = request.method

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
                "%s %s failed after %.2fms: %s",
                method,
                endpoint,
                duration_ms,
                e,
            )

            raise

        duration_seconds = time.perf_counter() - start_time
        duration_ms = duration_seconds * 1000

        status_code = str(response.status_code)

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
            "%s %s | %s | %.2fms",
            method,
            endpoint,
            status_code,
            duration_ms,
        )

        return response