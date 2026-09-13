import json

import pytest
from pydantic import TypeAdapter

from app.core.analytics import (
    AnalyticsSeverity,
    BurstStatus,
    ConfidenceLevel,
    MetricName,
    MissingValuePolicy,
    SortDirection,
)

ENUM_TYPES = (
    MetricName,
    MissingValuePolicy,
    SortDirection,
    AnalyticsSeverity,
    ConfidenceLevel,
    BurstStatus,
)


@pytest.mark.parametrize("enum_type", ENUM_TYPES)
def test_analytics_enum_values_remain_string_compatible(enum_type) -> None:
    for member in enum_type:
        assert isinstance(member, str)
        assert str(member) == member.value
        assert json.dumps(member) == json.dumps(member.value)


@pytest.mark.parametrize("enum_type", ENUM_TYPES)
def test_analytics_enum_json_schema_preserves_values(enum_type) -> None:
    schema = TypeAdapter(enum_type).json_schema()

    assert schema["enum"] == [member.value for member in enum_type]
    assert schema["type"] == "string"
