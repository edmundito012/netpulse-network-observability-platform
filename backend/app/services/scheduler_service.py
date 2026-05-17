import asyncio

from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session

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
from app.services.monitoring_service import MonitoringService
from app.services.snmp_service import SNMPService
from fastapi.encoders import jsonable_encoder

from app.api.websocket import dashboard_manager
from app.services.dashboard_service import DashboardService

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
            *[
                ping_device_task(device)
                for device in devices
            ],
            return_exceptions=True,
        )

        results_by_device_id = {}

        for result in ping_results:
            if isinstance(result, Exception):
                print(f"Ping task error: {result}")
                continue

            results_by_device_id[result["device_id"]] = result

        for device in devices:
            result = results_by_device_id.get(device.id)

            if not result:
                continue

            previous_status = device.status
            status = result["status"]

            device.status = status

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

                print(f"Alert created for device {device.id}")

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

                print(f"Alert resolved for device {device.id}")

        db.commit()

        print("Async device monitoring cycle completed")

    except Exception as e:
        db.rollback()
        print(f"Async monitoring error: {e}")

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
            *[
                collect_snmp_for_device(device)
                for device in devices
            ],
            return_exceptions=True,
        )

        devices_by_id = {
            device.id: device
            for device in devices
        }

        for result in snmp_results:
            if isinstance(result, Exception):
                print(f"SNMP task error: {result}")
                continue

            device = devices_by_id.get(result["device_id"])

            if not device:
                continue

            if not result["success"]:
                print(
                    f"SNMP snapshot error for device "
                    f"{device.id}: {result['error']}"
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

            print(f"SNMP snapshot collected for device {device.id}")

        print("Async SNMP snapshot cycle completed")

    except Exception as e:
        db.rollback()
        print(f"SNMP scheduler error: {e}")

    finally:
        db.close()



def collect_snmp_system_snapshots():
    asyncio.run(collect_snmp_system_snapshots_async())

async def broadcast_dashboard_overview():
    db: Session = SessionLocal()

    try:
        overview = DashboardService.get_overview(db=db)

        await dashboard_manager.broadcast(
            jsonable_encoder(overview)
        )

    except Exception as e:
        print(f"Dashboard broadcast error: {e}")

    finally:
        db.close()


def broadcast_dashboard_overview_job():
    asyncio.run(broadcast_dashboard_overview())


def start_scheduler():
    if scheduler.running:
        print("Monitoring scheduler already running")
        return

    scheduler.add_job(
        monitor_devices,
        "interval",
        seconds=30,
        id="monitor_devices",
        replace_existing=True,
    )

    scheduler.add_job(
        collect_snmp_system_snapshots,
        "interval",
        seconds=60,
        id="collect_snmp_system_snapshots",
        replace_existing=True,
    )

    scheduler.add_job(
        broadcast_dashboard_overview_job,
        "interval",
        seconds=5,
        id="broadcast_dashboard_overview",
        replace_existing=True,
    )

    scheduler.start()

    print("Monitoring scheduler started")


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)
        print("Monitoring scheduler stopped")