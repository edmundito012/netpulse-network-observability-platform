import json

from pydantic import TypeAdapter

from app.models.user import User, UserRole


def test_user_role_remains_string_compatible() -> None:
    for role in UserRole:
        assert isinstance(role, str)
        assert str(role) == role.value
        assert json.dumps(role) == json.dumps(role.value)


def test_user_role_json_schema_preserves_values() -> None:
    schema = TypeAdapter(UserRole).json_schema()

    assert schema["enum"] == ["ADMIN", "OPERATOR", "VIEWER"]
    assert schema["type"] == "string"


def test_user_role_sqlalchemy_contract_remains_stable() -> None:
    column_type = User.__table__.c.role.type

    assert column_type.name == "userrole"
    assert column_type.enums == ["ADMIN", "OPERATOR", "VIEWER"]
