from app.models.alert import AlertSeverity
from app.services.predictive_alert_service import (
    PredictiveAlertService,
)


class PredictiveAlertGenerationService:

    @staticmethod
    def build_latency_alert():

        return {
            "severity": AlertSeverity.WARNING,
            "title": "Predictive degradation detected",
            "message": (
                "Latency trend indicates potential "
                "network degradation."
            ),
        }

    @staticmethod
    def build_packet_loss_alert():

        return {
            "severity": AlertSeverity.WARNING,
            "title": "Predictive degradation detected",
            "message": (
                "Packet loss trend indicates potential "
                "network degradation."
            ),
        }

    @staticmethod
    def build_jitter_alert():

        return {
            "severity": AlertSeverity.WARNING,
            "title": "Predictive degradation detected",
            "message": (
                "Jitter trend indicates potential "
                "network degradation."
            ),
        }