from ping3 import ping

from app.models.device import DeviceStatus


class MonitoringService:

    @staticmethod
    def ping_device(ip_address: str) -> DeviceStatus:
        response_time = ping(
            str(ip_address),
            timeout=2
        )

        if response_time is None:
            return DeviceStatus.OFFLINE

        return DeviceStatus.ONLINE