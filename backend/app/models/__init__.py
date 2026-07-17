"""NetPulse SQLAlchemy model registry.

Importing the model package registers every persistence model in the
shared SQLAlchemy declarative registry. Relationship targets referenced
by string names must be imported here before mapper configuration.
"""

from app.models.alert import (
    Alert,
    AlertSeverity,
    AlertStatus,
    AlertType,
)
from app.models.audit_log import AuditLog
from app.models.device import (
    Device,
    DeviceStatus,
)
from app.models.device_event import (
    DeviceEvent,
    DeviceEventType,
)
from app.models.device_metric import DeviceMetric
from app.models.device_snmp_system_snapshot import (
    DeviceSNMPSystemSnapshot,
)
from app.models.incident import (
    Incident,
    IncidentPriority,
    IncidentSeverity,
    IncidentSource,
    IncidentStatus,
)
from app.models.incident_alert import IncidentAlert
from app.models.incident_timeline_event import (
    IncidentTimelineActorType,
    IncidentTimelineEvent,
    IncidentTimelineEventType,
)
from app.models.notification_log import (
    NotificationLog,
)
from app.models.user import (
    User,
    UserRole,
)


__all__ = [
    "Alert",
    "AlertSeverity",
    "AlertStatus",
    "AlertType",
    "AuditLog",
    "Device",
    "DeviceEvent",
    "DeviceEventType",
    "DeviceMetric",
    "DeviceSNMPSystemSnapshot",
    "DeviceStatus",
    "Incident",
    "IncidentAlert",
    "IncidentPriority",
    "IncidentSeverity",
    "IncidentSource",
    "IncidentStatus",
    "IncidentTimelineActorType",
    "IncidentTimelineEvent",
    "IncidentTimelineEventType",
    "NotificationLog",
    "User",
    "UserRole",
]