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

    @staticmethod
    def get_paginated(
        db: Session,
        device_id: int | None = None,
        event_type: DeviceEventType | None = None,
        page: int = 1,
        page_size: int = 20,
    ):

        query = db.query(DeviceEvent)

        if device_id is not None:
            query = query.filter(DeviceEvent.device_id == device_id)

        if event_type is not None:
            query = query.filter(DeviceEvent.event_type == event_type)

        total_count = query.count()

        items = (
            query
            .order_by(DeviceEvent.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        total_pages = (
            (total_count + page_size - 1) // page_size
            if total_count > 0
            else 0
        )

        return {
            "items": items,
            "total_count": total_count,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }