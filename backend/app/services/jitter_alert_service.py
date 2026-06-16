from app.models.alert import AlertSeverity


class JitterAlertService:

    WARNING_THRESHOLD = 40
    CRITICAL_THRESHOLD = 60

    @staticmethod
    def evaluate(
        device_name: str,
        jitter_ms: float,
    ):
        if jitter_ms >= JitterAlertService.CRITICAL_THRESHOLD:

            return (
                AlertSeverity.CRITICAL,
                f"Critical jitter detected on {device_name}: "
                f"{jitter_ms:.2f} ms"
            )

        if jitter_ms >= JitterAlertService.WARNING_THRESHOLD:

            return (
                AlertSeverity.WARNING,
                f"High jitter detected on {device_name}: "
                f"{jitter_ms:.2f} ms"
            )

        return None