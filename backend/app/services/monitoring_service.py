import asyncio

from ping3 import ping

from app.core.config import settings
from app.core.logging import logger
from app.models.device import DeviceStatus


class MonitoringService:

    @staticmethod
    def ping_device(ip_address: str) -> tuple[DeviceStatus, float | None]:
        try:
            response_time = ping(
                str(ip_address),
                timeout=settings.PING_TIMEOUT_SECONDS,
            )

            if response_time is None:
                logger.warning(
                    "Ping failed for device IP %s after %ss timeout",
                    ip_address,
                    settings.PING_TIMEOUT_SECONDS,
                )

                return DeviceStatus.OFFLINE, None

            response_time_ms = response_time * 1000

            logger.info(
                "Ping successful for device IP %s: %.2f ms",
                ip_address,
                response_time_ms,
            )

            return DeviceStatus.ONLINE, response_time_ms

        except Exception as e:
            logger.error(
                "Ping error for device IP %s: %s",
                ip_address,
                e,
            )

            return DeviceStatus.OFFLINE, None

    @staticmethod
    async def ping_device_async(
        ip_address: str,
    ) -> tuple[DeviceStatus, float | None]:
        return await asyncio.to_thread(
            MonitoringService.ping_device,
            ip_address,
        )