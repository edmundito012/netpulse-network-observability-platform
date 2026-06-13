import asyncio

from ping3 import ping

from app.core.config import settings
from app.core.logging import logger
from app.models.device import DeviceStatus


class MonitoringService:

    @staticmethod
    def ping_device(
        ip_address: str,
        attempts: int = 5,
    ) -> tuple[DeviceStatus, float | None, float, float]:
        successful_pings: list[float] = []

        try:
            for _ in range(attempts):
                response_time = ping(
                    str(ip_address),
                    timeout=settings.PING_TIMEOUT_SECONDS,
                )

                if response_time is not None:
                    successful_pings.append(response_time)

            failed_pings = attempts - len(successful_pings)

            packet_loss_percent = (failed_pings / attempts) * 100

            if not successful_pings:
                logger.warning(
                    "Ping failed for device IP %s after %s attempts",
                    ip_address,
                    attempts,
                )

                return (
                    DeviceStatus.OFFLINE,
                    None,
                    packet_loss_percent,
                    0.0,
                )

            average_response_time_ms = (
                sum(successful_pings) / len(successful_pings)
            ) * 1000

            jitter_ms = 0.0

            if len(successful_pings) >= 2:

                differences = []

                for i in range(1, len(successful_pings)):
                    differences.append(
                        abs(
                            successful_pings[i]
                            - successful_pings[i - 1]
                        )
                    )

                jitter_ms = (
                    sum(differences)
                    / len(differences)
                ) * 1000

            logger.info(
                "Ping successful for device IP %s: %.2f ms avg, %.2f%% packet loss, %.2f ms jitter",
                ip_address,
                average_response_time_ms,
                packet_loss_percent,
                jitter_ms,
            )

            return (
                DeviceStatus.ONLINE,
                average_response_time_ms,
                packet_loss_percent,
                jitter_ms,
            )

        except Exception as e:
            logger.error(
                "Ping error for device IP %s: %s",
                ip_address,
                e,
            )

            return (
                DeviceStatus.OFFLINE,
                None,
                100.0,
                0.0,
            )

    @staticmethod
    async def ping_device_async(
        ip_address: str,
    ) -> tuple[DeviceStatus, float | None, float, float]:
        return await asyncio.to_thread(
            MonitoringService.ping_device,
            ip_address,
        )