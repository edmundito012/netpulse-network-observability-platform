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


scheduler = BackgroundScheduler()


def monitor_devices():
    db: Session = SessionLocal()

    try:
        devices = DeviceRepository.get_all(db)

        for device in devices:
            previous_status = device.status

            status, response_time_ms = MonitoringService.ping_device(
                device.ip_address,
            )

            device.status = status

            active_alert = AlertRepository.get_active_alert_for_device(
                db=db,
                device_id=device.id,
            )

            if status == DeviceStatus.OFFLINE and previous_status != DeviceStatus.OFFLINE:
                DeviceEventRepository.create(
                    db=db,
                    device_id=device.id,
                    event_type=DeviceEventType.DEVICE_OFFLINE,
                    message=f"Device {device.name} changed status to OFFLINE",
                )

            if status == DeviceStatus.ONLINE and previous_status != DeviceStatus.ONLINE:
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

        print("Device monitoring cycle completed")

    except Exception as e:
        db.rollback()
        print(f"Monitoring error: {e}")

    finally:
        db.close()


async def collect_snmp_system_snapshots_async():
    db: Session = SessionLocal()

    try:
        devices = DeviceRepository.get_all(db)

        for device in devices:
            try:
                system_info = await SNMPService.get_system_info(
                    ip_address=device.ip_address,
                )

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
                    message=f"SNMP system snapshot collected for device {device.name}",
                )

                print(f"SNMP snapshot collected for device {device.id}")

            except Exception as e:
                print(f"SNMP snapshot error for device {device.id}: {e}")

        print("SNMP snapshot cycle completed")

    except Exception as e:
        db.rollback()
        print(f"SNMP scheduler error: {e}")

    finally:
        db.close()


def collect_snmp_system_snapshots():
    asyncio.run(collect_snmp_system_snapshots_async())


def start_scheduler():
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

    scheduler.start()

    print("Monitoring scheduler started")