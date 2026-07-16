"""Application service for monitored network devices."""

from sqlalchemy.orm import Session

from app.repositories.alert_repository import (
    AlertRepository,
)
from app.repositories.device_metric_repository import (
    DeviceMetricRepository,
)
from app.repositories.device_repository import (
    DeviceRepository,
)
from app.schemas.device import (
    DeviceCreate,
    DeviceUpdate,
)
from app.services.alert_service import AlertService
from app.services.flapping_alert_service import (
    FlappingAlertService,
)
from app.services.jitter_alert_service import (
    JitterAlertService,
)
from app.services.latency_alert_service import (
    LatencyAlertService,
)
from app.services.monitoring_service import (
    MonitoringService,
)
from app.services.packet_loss_burst_incident_service import (
    PacketLossBurstIncidentService,
)


class DeviceService:
    """Coordinate device persistence and monitoring operations."""

    @staticmethod
    def get_devices(
        db: Session,
    ):
        return DeviceRepository.get_all(db)

    @staticmethod
    def get_device(
        db: Session,
        device_id: int,
    ):
        device = DeviceRepository.get_by_id(
            db,
            device_id,
        )

        if not device:
            raise ValueError(
                "Device not found"
            )

        return device

    @staticmethod
    def create_device(
        db: Session,
        device_data: DeviceCreate,
    ):
        existing_device = (
            DeviceRepository.get_by_ip_address(
                db,
                device_data.ip_address,
            )
        )

        if existing_device:
            raise ValueError(
                "Device with this IP address "
                "already exists"
            )

        return DeviceRepository.create(
            db=db,
            device_data=device_data,
        )

    @staticmethod
    def update_device(
        db: Session,
        device_id: int,
        device_data: DeviceUpdate,
    ):
        device = DeviceRepository.get_by_id(
            db,
            device_id,
        )

        if not device:
            raise ValueError(
                "Device not found"
            )

        return DeviceRepository.update(
            db=db,
            device=device,
            device_data=device_data,
        )

    @staticmethod
    def delete_device(
        db: Session,
        device_id: int,
    ):
        device = DeviceRepository.get_by_id(
            db,
            device_id,
        )

        if not device:
            raise ValueError(
                "Device not found"
            )

        DeviceRepository.delete(
            db=db,
            device=device,
        )

        return None

    @staticmethod
    def ping_device(
        db: Session,
        device_id: int,
    ):
        """Collect a metric and execute operational evaluations."""

        device = DeviceRepository.get_by_id(
            db,
            device_id,
        )

        if not device:
            raise ValueError(
                "Device not found"
            )

        (
            device_status,
            response_time_ms,
            packet_loss_percent,
            jitter_ms,
        ) = MonitoringService.ping_device(
            device.ip_address,
        )

        device.status = device_status

        DeviceMetricRepository.create(
            db=db,
            device_id=device.id,
            status=device_status,
            response_time_ms=response_time_ms,
            packet_loss_percent=packet_loss_percent,
            jitter_ms=jitter_ms,
        )

        jitter_alert = JitterAlertService.evaluate(
            device_name=device.name,
            jitter_ms=jitter_ms,
        )

        if jitter_alert:
            severity, message = jitter_alert

            AlertRepository.create(
                db=db,
                device_id=device.id,
                severity=severity,
                message=message,
            )

        AlertService.create_packet_loss_alert_if_needed(
            db=db,
            device_id=device.id,
            device_name=device.name,
            packet_loss_percent=packet_loss_percent,
        )

        LatencyAlertService.create_latency_trend_alert_if_needed(
            db=db,
            device_id=device.id,
            device_name=device.name,
        )

        FlappingAlertService.create_flapping_alert_if_needed(
            db=db,
            device_id=device.id,
            device_name=device.name,
        )

        PacketLossBurstIncidentService.evaluate(
            db=db,
            device_id=device.id,
            device_name=device.name,
        )

        db.refresh(device)

        return device