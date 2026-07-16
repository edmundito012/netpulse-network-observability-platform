"""Domain exceptions raised by the Incident Engine."""


class IncidentError(Exception):
    """Base exception for Incident Engine operations."""


class IncidentNotFoundError(IncidentError):
    """Raised when an incident cannot be found."""

    def __init__(
        self,
        incident_identifier: int | str,
    ) -> None:
        super().__init__(
            f"Incident {incident_identifier!r} was not found"
        )


class IncidentOwnerNotFoundError(IncidentError):
    """Raised when an incident owner does not exist."""

    def __init__(
        self,
        owner_id: int,
    ) -> None:
        super().__init__(
            f"User {owner_id} was not found"
        )


class IncidentAlertNotFoundError(IncidentError):
    """Raised when an alert cannot be found."""

    def __init__(
        self,
        alert_id: int,
    ) -> None:
        super().__init__(
            f"Alert {alert_id} was not found"
        )


class IncidentAlertConflictError(IncidentError):
    """Raised when an alert belongs to another incident."""

    def __init__(
        self,
        *,
        alert_id: int,
        public_id: str,
    ) -> None:
        super().__init__(
            f"Alert {alert_id} is already attached "
            f"to incident {public_id}"
        )


class IncidentAlertNotAttachedError(IncidentError):
    """Raised when detaching an unrelated alert."""

    def __init__(
        self,
        *,
        alert_id: int,
        public_id: str,
    ) -> None:
        super().__init__(
            f"Alert {alert_id} is not attached "
            f"to incident {public_id}"
        )


class InvalidIncidentTransitionError(IncidentError):
    """Raised when an incident lifecycle transition is invalid."""

    def __init__(
        self,
        *,
        current_status: str,
        target_status: str,
    ) -> None:
        super().__init__(
            "Invalid incident transition: "
            f"{current_status} -> {target_status}"
        )


class IncidentResolutionError(IncidentError):
    """Raised when an incident cannot be resolved."""

    def __init__(
        self,
        message: str,
    ) -> None:
        super().__init__(message)