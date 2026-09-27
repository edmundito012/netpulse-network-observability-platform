from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from app.models.device import DeviceStatus
from app.services.scheduler_service import ping_device_task


@pytest.mark.asyncio
async def test_ping_device_task_preserves_jitter():
    device = SimpleNamespace(
        id=17,
        ip_address="192.168.0.1",
    )

    ping_result = (
        DeviceStatus.ONLINE,
        4.48,
        0.0,
        0.95,
    )

    with patch(
        "app.services.scheduler_service.MonitoringService.ping_device_async",
        new_callable=AsyncMock,
        return_value=ping_result,
    ) as ping_device:
        result = await ping_device_task(device)

    ping_device.assert_awaited_once_with("192.168.0.1")

    assert result == {
        "device_id": 17,
        "status": DeviceStatus.ONLINE,
        "response_time_ms": 4.48,
        "packet_loss_percent": 0.0,
        "jitter_ms": 0.95,
    }
