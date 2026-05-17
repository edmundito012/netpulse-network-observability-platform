import asyncio
from datetime import UTC, datetime

from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session

from app.api.websocket import dashboard_manager, device_state_manager
from app.core.config import settings
from app.core.device_state_cache import (
    get_all_device_states,
    update_device_state,
)
from app.core.logging import logger
from app.db.session import SessionLocal
from app.models.alert import AlertSeverity
from app.models.device import DeviceStatus
from app.models.device_event import DeviceEventType
from app.repositories.alert_repository import AlertRepository
from app.repositories.device_event_repository import DeviceEventRepository
from app.repositories.device_repository import DeviceRepository
from app.repositories.device_snmp_system_snapshot_repository import (
    DeviceSNMPSystemSnapshotRepository,
)
from app.services.dashboard_service import DashboardService
from app.services.monitoring_service import MonitoringService
from app.services.snmp_service import SNMPService


scheduler = BackgroundScheduler()


async def ping_device_task(device):
    status, response_time_ms = await MonitoringService.ping_device_async(
        device.ip_address,
    )

    return {
        "device_id": device.id,
        "status": status,
        "response_time_ms": response_time_ms,
    }


async def monitor_devices_async():
    db: Session = SessionLocal()

    try:
        devices = DeviceRepository.get_all(db)

        ping_results = await asyncio.gather(
            *[ping_device_task(device) for device in devices],
            return_exceptions=True,
        )

        results_by_device_id = {}

        for result in ping_results:
            if isinstance(result, Exception):
                logger.error("Ping task error: %s", result)
                continue

            results_by_device_id[result["device_id"]] = result

        for device in devices:
            result = results_by_device_id.get(device.id)

            if not result:
                continue

            previous_status = device.status
            status = result["status"]

            device.status = status

            update_device_state(
                device.id,
                {
                    "device_id": device.id,
                    "device_name": device.name,
                    "ip_address": device.ip_address,
                    "status": status,
                    "response_time_ms": result["response_time_ms"],
                    "last_checked_at": datetime.now(UTC).isoformat(),
                },
            )

            active_alert = AlertRepository.get_active_alert_for_device(
                db=db,
                device_id=device.id,
            )

            if (
                status == DeviceStatus.OFFLINE
                and previous_status != DeviceStatus.OFFLINE
            ):
                DeviceEventRepository.create(
                    db=db,
                    device_id=device.id,
                    event_type=DeviceEventType.DEVICE_OFFLINE,
                    message=f"Device {device.name} changed status to OFFLINE",
                )

                logger.warning(
                    "Device %s changed status to OFFLINE",
                    device.id,
                )

            if (
                status == DeviceStatus.ONLINE
                and previous_status != DeviceStatus.ONLINE
            ):
                DeviceEventRepository.create(
                    db=db,
                    device_id=device.id,
                    event_type=DeviceEventType.DEVICE_ONLINE,
                    message=f"Device {device.name} changed status to ONLINE",
                )

                logger.info(
                    "Device %s changed status to ONLINE",
                    device.id,
                )

            if status == DeviceStatus.OFFLINE and not active_alert:
                alert = AlertRepository.create(
                    db=db,
                    device_id=device.id,
                    severity=AlertSeverity.CRITICAL,
                    message=f"Device {device.name} is offline",
                )

                DeviceEventRepository.create(
                    db=db,
                    device_id=device.id,
                    event_type=DeviceEventType.ALERT_CREATED,
                    message=f"Critical alert created: {alert.message}",
                )

                logger.warning(
                    "Critical alert created for device %s",
                    device.id,
                )

            if status == DeviceStatus.ONLINE and active_alert:
                resolved_alert = AlertRepository.resolve(
                    db=db,
                    alert=active_alert,
                )

                DeviceEventRepository.create(
                    db=db,
                    device_id=device.id,
                    event_type=DeviceEventType.ALERT_RESOLVED,
                    message=f"Alert resolved: {resolved_alert.message}",
                )

                logger.info(
                    "Alert resolved for device %s",
                    device.id,
                )

        db.commit()

        await device_state_manager.broadcast(
            get_all_device_states()
        )

        logger.info("Async device monitoring cycle completed")

    except Exception as e:
        db.rollback()
        logger.error("Async monitoring error: %s", e)

    finally:
        db.close()


def monitor_devices():
    asyncio.run(monitor_devices_async())


async def collect_snmp_for_device(device):
    try:
        system_info = await SNMPService.get_system_info(
            ip_address=device.ip_address,
        )

        return {
            "device_id": device.id,
            "success": True,
            "system_info": system_info,
        }

    except Exception as e:
        return {
            "device_id": device.id,
            "success": False,
            "error": str(e),
        }


async def collect_snmp_system_snapshots_async():
    db: Session = SessionLocal()

    try:
        devices = DeviceRepository.get_all(db)

        snmp_results = await asyncio.gather(
            *[collect_snmp_for_device(device) for device in devices],
            return_exceptions=True,
        )

        devices_by_id = {device.id: device for device in devices}

        for result in snmp_results:
            if isinstance(result, Exception):
                logger.error("SNMP task error: %s", result)
                continue

            device = devices_by_id.get(result["device_id"])

            if not device:
                continue

            if not result["success"]:
                logger.warning(
                    "SNMP snapshot error for device %s: %s",
                    device.id,
                    result["error"],
                )
                continue

            system_info = result["system_info"]

            DeviceSNMPSystemSnapshotRepository.create(
                db=db,
                device_id=device.id,
                sysdescr=system_info.get("sysdescr"),
                sysuptime=system_info.get("sysuptime"),
                syscontact=system_info.get("syscontact"),
                sysname=system_info.get("sysname"),
                syslocation=system_info.get("syslocation"),
            )

            DeviceEventRepository.create(
                db=db,
                device_id=device.id,
                event_type=DeviceEventType.SNMP_SNAPSHOT_COLLECTED,
                message=(
                    "SNMP system snapshot collected for device "
                    f"{device.name}"
                ),
            )

            logger.info(
                "SNMP snapshot collected for device %s",
                device.id,
            )

        db.commit()

        logger.info("Async SNMP snapshot cycle completed")

    except Exception as e:
        db.rollback()
        logger.error("SNMP scheduler error: %s", e)

    finally:
        db.close()


def collect_snmp_system_snapshots():
    asyncio.run(collect_snmp_system_snapshots_async())


async def broadcast_dashboard_overview():
    db: Session = SessionLocal()

    try:
        overview = DashboardService.refresh_dashboard_cache(db=db)

        await dashboard_manager.broadcast(overview)

    except Exception as e:
        logger.error("Dashboard broadcast error: %s", e)

    finally:
        db.close()


def broadcast_dashboard_overview_job():
    asyncio.run(broadcast_dashboard_overview())


def warm_up_caches():
    db: Session = SessionLocal()

    try:
        DashboardService.refresh_dashboard_cache(db=db)
        logger.info("Dashboard cache warmed up")

    except Exception as e:
        logger.error("Cache warm-up error: %s", e)

    finally:
        db.close()


def start_scheduler():
    if scheduler.running:
        logger.info("Monitoring scheduler already running")
        return

    scheduler.add_job(
        monitor_devices,
        "interval",
        seconds=settings.MONITOR_INTERVAL_SECONDS,
        id="monitor_devices",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )

    scheduler.add_job(
        collect_snmp_system_snapshots,
        "interval",
        seconds=settings.SNMP_INTERVAL_SECONDS,
        id="collect_snmp_system_snapshots",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )

    scheduler.add_job(
        broadcast_dashboard_overview_job,
        "interval",
        seconds=settings.DASHBOARD_BROADCAST_INTERVAL_SECONDS,
        id="broadcast_dashboard_overview",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )

    warm_up_caches()

    scheduler.start()

    logger.info(
        "Monitoring scheduler started with intervals: monitor=%ss snmp=%ss dashboard=%ss",
        settings.MONITOR_INTERVAL_SECONDS,
        settings.SNMP_INTERVAL_SECONDS,
        settings.DASHBOARD_BROADCAST_INTERVAL_SECONDS,
    )


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Monitoring scheduler stopped")