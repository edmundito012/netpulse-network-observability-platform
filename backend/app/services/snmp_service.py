from pysnmp.hlapi.v3arch.asyncio import (
    CommunityData,
    ContextData,
    ObjectIdentity,
    ObjectType,
    SnmpEngine,
    UdpTransportTarget,
    get_cmd,
)


class SNMPService:

    @staticmethod
    async def get_value(
        ip_address: str,
        oid: str,
        community: str = "public",
        port: int = 1161,
        timeout: int = 2,
        retries: int = 1,
    ):
        error_indication, error_status, error_index, var_binds = await get_cmd(
            SnmpEngine(),
            CommunityData(community),
            await UdpTransportTarget.create(
                (str(ip_address), port),
                timeout=timeout,
                retries=retries,
            ),
            ContextData(),
            ObjectType(ObjectIdentity(oid)),
        )

        if error_indication:
            raise ValueError(str(error_indication))

        if error_status:
            raise ValueError(
                f"{error_status.prettyPrint()} at {error_index}"
            )

        for var_bind in var_binds:
            return str(var_bind[1])

        return None

    @staticmethod
    async def get_sysdescr(
        ip_address: str,
        community: str = "public",
        port: int = 1161,
    ):
        return await SNMPService.get_value(
            ip_address=ip_address,
            oid="1.3.6.1.2.1.1.1.0",
            community=community,
            port=port,
        )

    @staticmethod
    async def get_system_info(
        ip_address: str,
        community: str = "public",
        port: int = 1161,
    ):
        oids = {
            "sysdescr": "1.3.6.1.2.1.1.1.0",
            "sysuptime": "1.3.6.1.2.1.1.3.0",
            "syscontact": "1.3.6.1.2.1.1.4.0",
            "sysname": "1.3.6.1.2.1.1.5.0",
            "syslocation": "1.3.6.1.2.1.1.6.0",
        }

        result = {}

        for key, oid in oids.items():
            result[key] = await SNMPService.get_value(
                ip_address=ip_address,
                oid=oid,
                community=community,
                port=port,
            )

        return result