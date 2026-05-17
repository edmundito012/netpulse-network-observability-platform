import time

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging import logger


class RequestLoggingMiddleware(BaseHTTPMiddleware):

    async def dispatch(
        self,
        request: Request,
        call_next,
    ):
        start_time = time.perf_counter()

        try:
            response = await call_next(request)

        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000

            logger.error(
                "%s %s failed after %.2fms: %s",
                request.method,
                request.url.path,
                duration_ms,
                e,
            )

            raise

        duration_ms = (time.perf_counter() - start_time) * 1000

        logger.info(
            "%s %s | %s | %.2fms",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )

        return response