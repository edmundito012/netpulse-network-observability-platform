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
        device_id: int | None = None,
        event_type: DeviceEventType | None = None,
        limit: int = 100,
    ) -> list[DeviceEvent]:

        query = db.query(DeviceEvent)

        if device_id is not None:
            query = query.filter(
                DeviceEvent.device_id == device_id
            )

        if event_type is not None:
            query = query.filter(
                DeviceEvent.event_type == event_type
            )

        return (
            query
            .order_by(DeviceEvent.created_at.desc())
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_by_device(
        db: Session,
        device_id: int,
        limit: int = 100,
    ) -> list[DeviceEvent]:

        return (
            db.query(DeviceEvent)
            .filter(DeviceEvent.device_id == device_id)
            .order_by(DeviceEvent.created_at.desc())
            .limit(limit)
            .all()
        )