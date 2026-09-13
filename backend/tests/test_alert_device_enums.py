import json

import pytest
from pydantic import TypeAdapter

from app.models.alert import Alert, AlertSeverity, AlertStatus, AlertType
from app.models.device import Device, DeviceStatus
from app.models.device_event import DeviceEvent, DeviceEventType

ENUM_TYPES = (
    AlertSeverity,
    AlertStatus,
    AlertType,
    DeviceStatus,
    DeviceEventType,
)


@pytest.mark.parametrize("enum_type", ENUM_TYPES)
def test_alert_device_enums_remain_string_compatible(enum_type) -> None:
    for member in enum_type:
        assert isinstance(member, str)
        assert str(member) == member.value
        assert json.dumps(member) == json.dumps(member.value)


@pytest.mark.parametrize("enum_type", ENUM_TYPES)
def test_alert_device_enum_json_schema_preserves_values(enum_type) -> None:
    schema = TypeAdapter(enum_type).json_schema()

    assert schema["enum"] == [member.value for member in enum_type]
    assert schema["type"] == "string"


@pytest.mark.parametrize(
    ("column_type", "enum_type"),
    (
        (Alert.__table__.c.alert_type.type, AlertType),
        (Alert.__table__.c.severity.type, AlertSeverity),
        (Alert.__table__.c.status.type, AlertStatus),
        (Device.__table__.c.status.type, DeviceStatus),
        (DeviceEvent.__table__.c.event_type.type, DeviceEventType),
    ),
)
def test_sqlalchemy_enum_member_names_remain_stable(
    column_type,
    enum_type,
) -> None:
    assert column_type.enums == [member.name for member in enum_type]
