from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.repositories.device_repository import DeviceRepository
from app.services.monitoring_service import MonitoringService


scheduler = BackgroundScheduler()


def monitor_devices():
    db: Session = SessionLocal()

    try:
        devices = DeviceRepository.get_all(db)

        for device in devices:
            status = MonitoringService.ping_device(device.ip_address)

            device.status = status

        db.commit()

        print("Device monitoring cycle completed")

    except Exception as e:
        print(f"Monitoring error: {e}")

    finally:
        db.close()


def start_scheduler():
    scheduler.add_job(
        monitor_devices,
        "interval",
        seconds=30
    )

    scheduler.start()

    print("Monitoring scheduler started")