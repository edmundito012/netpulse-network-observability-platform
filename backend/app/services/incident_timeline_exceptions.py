"""Domain exceptions raised by Incident Timeline operations."""


class IncidentTimelineError(Exception):
    """Base exception for timeline operations."""


class IncidentTimelineActorError(
    IncidentTimelineError
):
    """Raised when timeline actor information is invalid."""


class IncidentTimelineEventNotFoundError(
    IncidentTimelineError
):
    """Raised when a timeline event cannot be found."""

    def __init__(
        self,
        event_id: int,
    ) -> None:
        super().__init__(
            f"Incident timeline event {event_id} "
            "was not found"
        )