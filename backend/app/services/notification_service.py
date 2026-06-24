from dataclasses import dataclass


@dataclass
class NotificationMessage:
    title: str
    body: str


class NotificationService:

    @staticmethod
    def build_predictive_alert_message(
        device_name: str,
        risk_score: int,
        reason: str,
    ) -> NotificationMessage:

        return NotificationMessage(
            title="Predictive Alert",
            body=(
                f"Device: {device_name}\n"
                f"Risk Score: {risk_score}\n"
                f"Reason: {reason}"
            ),
        )

    @staticmethod
    def build_network_risk_message(
        risk_score: int,
        risk_level: str,
    ) -> NotificationMessage:

        return NotificationMessage(
            title="Network Risk Alert",
            body=(
                f"Risk Score: {risk_score}\n"
                f"Risk Level: {risk_level}"
            ),
        )