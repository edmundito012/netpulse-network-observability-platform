from app.models.device_metric import DeviceMetric


class PredictiveAlertService:

    TREND_WINDOW = 5

    @staticmethod
    def is_increasing(values: list[float]) -> bool:
        if len(values) < PredictiveAlertService.TREND_WINDOW:
            return False

        return all(
            values[i] < values[i + 1]
            for i in range(len(values) - 1)
        )

    @staticmethod
    def detect_latency_trend(
        metrics: list[DeviceMetric],
    ) -> bool:

        latencies = [
            metric.response_time_ms or 0
            for metric in metrics
        ]

        return PredictiveAlertService.is_increasing(
            latencies
        )

    @staticmethod
    def detect_packet_loss_trend(
        metrics: list[DeviceMetric],
    ) -> bool:

        packet_loss = [
            metric.packet_loss_percent or 0
            for metric in metrics
        ]

        return PredictiveAlertService.is_increasing(
            packet_loss
        )

    @staticmethod
    def detect_jitter_trend(
        metrics: list[DeviceMetric],
    ) -> bool:

        jitters = [
            metric.jitter_ms or 0
            for metric in metrics
        ]

        return PredictiveAlertService.is_increasing(
            jitters
        )