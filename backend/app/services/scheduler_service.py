import asyncio

from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
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
            status, response_time_ms = MonitoringService.ping_device(device.ip_address)
            device.status = status

        db.commit()

        print("Device monitoring cycle completed")

    except Exception as e:
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

                print(f"SNMP snapshot collected for device {device.id}")

            except Exception as e:
                print(f"SNMP snapshot error for device {device.id}: {e}")

        print("SNMP snapshot cycle completed")

    except Exception as e:
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