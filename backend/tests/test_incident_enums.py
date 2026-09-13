import json

import pytest
from pydantic import TypeAdapter

from app.models.incident import (
    Incident,
    IncidentPriority,
    IncidentSeverity,
    IncidentSource,
    IncidentStatus,
)
from app.models.incident_timeline_event import (
    IncidentTimelineActorType,
    IncidentTimelineEvent,
    IncidentTimelineEventType,
)

ENUM_TYPES = (
    IncidentStatus,
    IncidentSeverity,
    IncidentPriority,
    IncidentSource,
    IncidentTimelineEventType,
    IncidentTimelineActorType,
)


@pytest.mark.parametrize("enum_type", ENUM_TYPES)
def test_incident_enums_remain_string_compatible(enum_type) -> None:
    for member in enum_type:
        assert isinstance(member, str)
        assert str(member) == member.value
        assert json.dumps(member) == json.dumps(member.value)


@pytest.mark.parametrize("enum_type", ENUM_TYPES)
def test_incident_enum_json_schema_preserves_values(enum_type) -> None:
    schema = TypeAdapter(enum_type).json_schema()

    assert schema["enum"] == [member.value for member in enum_type]
    assert schema["type"] == "string"


@pytest.mark.parametrize(
    ("column_type", "enum_type"),
    (
        (Incident.__table__.c.status.type, IncidentStatus),
        (Incident.__table__.c.severity.type, IncidentSeverity),
        (Incident.__table__.c.priority.type, IncidentPriority),
        (Incident.__table__.c.source.type, IncidentSource),
        (
            IncidentTimelineEvent.__table__.c.event_type.type,
            IncidentTimelineEventType,
        ),
        (
            IncidentTimelineEvent.__table__.c.actor_type.type,
            IncidentTimelineActorType,
        ),
    ),
)
def test_sqlalchemy_incident_enum_names_remain_stable(
    column_type,
    enum_type,
) -> None:
    assert column_type.enums == [member.name for member in enum_type]
