from sqlalchemy.orm import Session

from app.models.device_event import DeviceEvent, DeviceEventType


class DeviceEventRepository:
    @staticmethod
    def create(
        db: Session,
        device_id: int,
        event_type: DeviceEventType,
        message: str,
    ) -> DeviceEvent:
        event = DeviceEvent(
            device_id=device_id,
            event_type=event_type,
            message=message,
        )

        db.add(event)
        db.commit()
        db.refresh(event)

        return event

    @staticmethod
    def get_all(
        db: Session,
        limit: int = 100,
    ):
        return (
            db.query(DeviceEvent)
            .order_by(DeviceEvent.created_at.desc())
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_by_device(
        db: Session,
        device_id: int,
        limit: int = 100,
    ):
        return (
            db.query(DeviceEvent)
            .filter(DeviceEvent.device_id == device_id)
            .order_by(DeviceEvent.created_at.desc())
            .limit(limit)
            .all()
        )