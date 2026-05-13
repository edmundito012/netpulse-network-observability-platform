from sqlalchemy.orm import Session

from app.models.device import Device
from app.schemas.device import DeviceCreate, DeviceUpdate


class DeviceRepository:

    @staticmethod
    def get_all(db: Session):
        return db.query(Device).all()

    @staticmethod
    def get_by_id(db: Session, device_id: int):
        return db.query(Device).filter(Device.id == device_id).first()

    @staticmethod
    def get_by_ip_address(db: Session, ip_address: str):
        return db.query(Device).filter(Device.ip_address == str(ip_address)).first()

    @staticmethod
    def create(db: Session, device_data: DeviceCreate):
        db_device = Device(
            name=device_data.name,
            ip_address=str(device_data.ip_address),
            hostname=device_data.hostname,
            device_type=device_data.device_type,
            location=device_data.location,
            status=device_data.status,
        )

        db.add(db_device)
        db.commit()
        db.refresh(db_device)

        return db_device

    @staticmethod
    def update(db: Session, device: Device, device_data: DeviceUpdate):
        update_data = device_data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            if field == "ip_address" and value is not None:
                value = str(value)

            setattr(device, field, value)

        db.commit()
        db.refresh(device)

        return device

    @staticmethod
    def delete(db: Session, device: Device):
        db.delete(device)
        db.commit()
        return None