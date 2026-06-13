from sqlalchemy.orm import Session

from app.repositories.device_metric_repository import DeviceMetricRepository
from app.repositories.device_repository import DeviceRepository
from app.schemas.device import DeviceCreate, DeviceUpdate
from app.services.alert_service import AlertService
from app.services.monitoring_service import MonitoringService


class DeviceService:

    @staticmethod
    def get_devices(db: Session):
        return DeviceRepository.get_all(db)

    @staticmethod
    def get_device(db: Session, device_id: int):
        device = DeviceRepository.get_by_id(db, device_id)

        if not device:
            raise ValueError("Device not found")

        return device

    @staticmethod
    def create_device(db: Session, device_data: DeviceCreate):
        existing_device = DeviceRepository.get_by_ip_address(
            db,
            device_data.ip_address,
        )

        if existing_device:
            raise ValueError("Device with this IP address already exists")

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
        device = DeviceRepository.get_by_id(db, device_id)

        if not device:
            raise ValueError("Device not found")

        return DeviceRepository.update(
            db=db,
            device=device,
            device_data=device_data,
        )

    @staticmethod
    def delete_device(db: Session, device_id: int):
        device = DeviceRepository.get_by_id(db, device_id)

        if not device:
            raise ValueError("Device not found")

        DeviceRepository.delete(
            db=db,
            device=device,
        )

        return None

    @staticmethod
    def ping_device(db: Session, device_id: int):
        device = DeviceRepository.get_by_id(db, device_id)

        if not device:
            raise ValueError("Device not found")

        (
            status,
            response_time_ms,
            packet_loss_percent,
        ) = MonitoringService.ping_device(
            device.ip_address,
        )

        device.status = status

        DeviceMetricRepository.create(
            db=db,
            device_id=device.id,
            status=status,
            response_time_ms=response_time_ms,
            packet_loss_percent=packet_loss_percent,
        )

        AlertService.create_packet_loss_alert_if_needed(
            db=db,
            device_id=device.id,
            device_name=device.name,
            packet_loss_percent=packet_loss_percent,
        )

        db.refresh(device)

        return device