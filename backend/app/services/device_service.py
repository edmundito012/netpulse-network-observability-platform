from sqlalchemy.orm import Session

from app.repositories.device_repository import DeviceRepository
from app.schemas.device import DeviceCreate, DeviceUpdate


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
            device_data.ip_address
        )

        if existing_device:
            raise ValueError("Device with this IP address already exists")

        return DeviceRepository.create(
            db=db,
            device_data=device_data
        )

    @staticmethod
    def update_device(
        db: Session,
        device_id: int,
        device_data: DeviceUpdate
    ):
        device = DeviceRepository.get_by_id(db, device_id)

        if not device:
            raise ValueError("Device not found")

        return DeviceRepository.update(
            db=db,
            device=device,
            device_data=device_data
        )

    @staticmethod
    def delete_device(db: Session, device_id: int):
        device = DeviceRepository.get_by_id(db, device_id)

        if not device:
            raise ValueError("Device not found")

        DeviceRepository.delete(
            db=db,
            device=device
        )

        return None