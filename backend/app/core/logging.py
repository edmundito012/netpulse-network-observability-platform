import logging


logging.basicConfig(
    level=logging.INFO,
    format=(
        "%(asctime)s | "
        "%(levelname)s | "
        "%(name)s | "
        "%(message)s"
    ),
)

logger = logging.getLogger("netpulse")

# Reduce APScheduler verbosity
logging.getLogger("apscheduler").setLevel(
    logging.WARNING
)