import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, call

import pytest

from app.services import snmp_service
from app.services.snmp_service import SNMPService


def patch_snmp_dependencies(monkeypatch, get_cmd):
    engine = object()
    community_data = object()
    transport = object()
    context = object()
    identity = object()
    object_type = object()

    create_transport = AsyncMock(return_value=transport)
    community_factory = Mock(return_value=community_data)
    identity_factory = Mock(return_value=identity)
    object_type_factory = Mock(return_value=object_type)

    monkeypatch.setattr(
        snmp_service,
        "SnmpEngine",
        Mock(return_value=engine),
    )
    monkeypatch.setattr(
        snmp_service,
        "CommunityData",
        community_factory,
    )
    monkeypatch.setattr(
        snmp_service,
        "UdpTransportTarget",
        SimpleNamespace(create=create_transport),
    )
    monkeypatch.setattr(
        snmp_service,
        "ContextData",
        Mock(return_value=context),
    )
    monkeypatch.setattr(
        snmp_service,
        "ObjectIdentity",
        identity_factory,
    )
    monkeypatch.setattr(
        snmp_service,
        "ObjectType",
        object_type_factory,
    )
    monkeypatch.setattr(snmp_service, "get_cmd", get_cmd)

    return SimpleNamespace(
        engine=engine,
        community_data=community_data,
        transport=transport,
        context=context,
        object_type=object_type,
        create_transport=create_transport,
        community_factory=community_factory,
        identity_factory=identity_factory,
        object_type_factory=object_type_factory,
    )


def test_get_value_returns_first_var_bind(monkeypatch):
    get_cmd = AsyncMock(
        return_value=(
            None,
            None,
            0,
            [(object(), "router-01")],
        )
    )
    dependencies = patch_snmp_dependencies(monkeypatch, get_cmd)

    result = asyncio.run(
        SNMPService.get_value(
            ip_address="192.0.2.10",
            oid="1.2.3",
            community="private",
            port=1161,
            timeout=4,
            retries=2,
        )
    )

    assert result == "router-01"
    dependencies.create_transport.assert_awaited_once_with(
        ("192.0.2.10", 1161),
        timeout=4,
        retries=2,
    )
    dependencies.community_factory.assert_called_once_with("private")
    dependencies.identity_factory.assert_called_once_with("1.2.3")
    get_cmd.assert_awaited_once_with(
        dependencies.engine,
        dependencies.community_data,
        dependencies.transport,
        dependencies.context,
        dependencies.object_type,
    )


def test_get_value_uses_configured_defaults(monkeypatch):
    get_cmd = AsyncMock(return_value=(None, None, 0, []))
    dependencies = patch_snmp_dependencies(monkeypatch, get_cmd)

    result = asyncio.run(
        SNMPService.get_value(
            ip_address="192.0.2.20",
            oid="1.2.3",
        )
    )

    assert result is None
    dependencies.create_transport.assert_awaited_once_with(
        (
            "192.0.2.20",
            snmp_service.settings.SNMP_PORT,
        ),
        timeout=snmp_service.settings.SNMP_TIMEOUT_SECONDS,
        retries=snmp_service.settings.SNMP_RETRIES,
    )


def test_get_value_raises_error_indication(monkeypatch):
    get_cmd = AsyncMock(
        return_value=(
            "request timed out",
            None,
            0,
            [],
        )
    )
    patch_snmp_dependencies(monkeypatch, get_cmd)

    with pytest.raises(ValueError, match="request timed out"):
        asyncio.run(
            SNMPService.get_value(
                ip_address="192.0.2.30",
                oid="1.2.3",
            )
        )


def test_get_value_raises_status_error(monkeypatch):
    error_status = Mock()
    error_status.__bool__ = Mock(return_value=True)
    error_status.prettyPrint.return_value = "noSuchName"
    get_cmd = AsyncMock(
        return_value=(
            None,
            error_status,
            3,
            [],
        )
    )
    patch_snmp_dependencies(monkeypatch, get_cmd)

    with pytest.raises(
        ValueError,
        match="noSuchName at 3",
    ):
        asyncio.run(
            SNMPService.get_value(
                ip_address="192.0.2.40",
                oid="1.2.3",
            )
        )


def test_get_value_reraises_transport_error(monkeypatch):
    get_cmd = AsyncMock(side_effect=RuntimeError("transport failed"))
    patch_snmp_dependencies(monkeypatch, get_cmd)

    with pytest.raises(RuntimeError, match="transport failed"):
        asyncio.run(
            SNMPService.get_value(
                ip_address="192.0.2.50",
                oid="1.2.3",
            )
        )


def test_get_sysdescr_uses_standard_oid(monkeypatch):
    get_value = AsyncMock(return_value="NetPulse router")
    monkeypatch.setattr(SNMPService, "get_value", get_value)

    result = asyncio.run(
        SNMPService.get_sysdescr(
            ip_address="192.0.2.60",
            community="private",
            port=1161,
        )
    )

    assert result == "NetPulse router"
    get_value.assert_awaited_once_with(
        ip_address="192.0.2.60",
        oid="1.3.6.1.2.1.1.1.0",
        community="private",
        port=1161,
    )


def test_get_system_info_collects_standard_oids(monkeypatch):
    get_value = AsyncMock(
        side_effect=[
            "description",
            "12345",
            "admin@example.com",
            "router-01",
            "Madrid",
        ]
    )
    monkeypatch.setattr(SNMPService, "get_value", get_value)

    result = asyncio.run(
        SNMPService.get_system_info(
            ip_address="192.0.2.70",
            community="private",
            port=1161,
        )
    )

    assert result == {
        "sysdescr": "description",
        "sysuptime": "12345",
        "syscontact": "admin@example.com",
        "sysname": "router-01",
        "syslocation": "Madrid",
    }
    assert get_value.await_args_list == [
        call(
            ip_address="192.0.2.70",
            oid="1.3.6.1.2.1.1.1.0",
            community="private",
            port=1161,
        ),
        call(
            ip_address="192.0.2.70",
            oid="1.3.6.1.2.1.1.3.0",
            community="private",
            port=1161,
        ),
        call(
            ip_address="192.0.2.70",
            oid="1.3.6.1.2.1.1.4.0",
            community="private",
            port=1161,
        ),
        call(
            ip_address="192.0.2.70",
            oid="1.3.6.1.2.1.1.5.0",
            community="private",
            port=1161,
        ),
        call(
            ip_address="192.0.2.70",
            oid="1.3.6.1.2.1.1.6.0",
            community="private",
            port=1161,
        ),
    ]
