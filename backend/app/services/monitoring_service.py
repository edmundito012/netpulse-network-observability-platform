import asyncio

from ping3 import ping

from app.models.device import DeviceStatus


class MonitoringService:

    @staticmethod
    def ping_device(ip_address: str) -> tuple[DeviceStatus, float | None]:
        response_time = ping(
            str(ip_address),
            timeout=2,
        )

        if response_time is None:
            return DeviceStatus.OFFLINE, None

        response_time_ms = response_time * 1000

        return DeviceStatus.ONLINE, response_time_ms

    @staticmethod
    async def ping_device_async(
        ip_address: str,
    ) -> tuple[DeviceStatus, float | None]:
        return await asyncio.to_thread(
            MonitoringService.ping_device,
            ip_address,
        )