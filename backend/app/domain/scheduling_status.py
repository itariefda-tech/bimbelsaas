from enum import StrEnum


class ClassStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class RoomStatus(StrEnum):
    AVAILABLE = "available"
    MAINTENANCE = "maintenance"
    INACTIVE = "inactive"
    RESERVED = "reserved"
    ARCHIVED = "archived"


class EnrollmentStatus(StrEnum):
    ACTIVE = "active"
    ENDED = "ended"


class ScheduleStatus(StrEnum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    ACTIVE = "active"
    COMPLETED = "completed"
    RESCHEDULED = "rescheduled"
    CANCELLED = "cancelled"
    PENDING_APPROVAL = "pending_approval"
    SUSPENDED = "suspended"


class SessionStatus(StrEnum):
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    ACTIVE = "active"
    COMPLETED = "completed"
    RESCHEDULED = "rescheduled"
    CANCELLED = "cancelled"
    SUSPENDED = "suspended"


class RescheduleRequestStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


BLOCKING_SCHEDULE_STATUSES = frozenset(
    {
        ScheduleStatus.DRAFT,
        ScheduleStatus.SCHEDULED,
        ScheduleStatus.CONFIRMED,
        ScheduleStatus.ACTIVE,
        ScheduleStatus.PENDING_APPROVAL,
    }
)

SCHEDULE_TRANSITIONS = {
    ScheduleStatus.DRAFT: {
        ScheduleStatus.SCHEDULED,
        ScheduleStatus.CANCELLED,
    },
    ScheduleStatus.SCHEDULED: {
        ScheduleStatus.CONFIRMED,
        ScheduleStatus.SUSPENDED,
        ScheduleStatus.CANCELLED,
    },
    ScheduleStatus.CONFIRMED: {
        ScheduleStatus.ACTIVE,
        ScheduleStatus.SUSPENDED,
        ScheduleStatus.CANCELLED,
    },
    ScheduleStatus.ACTIVE: {
        ScheduleStatus.COMPLETED,
        ScheduleStatus.SUSPENDED,
        ScheduleStatus.CANCELLED,
    },
    ScheduleStatus.SUSPENDED: {
        ScheduleStatus.SCHEDULED,
        ScheduleStatus.CANCELLED,
    },
    ScheduleStatus.COMPLETED: set(),
    ScheduleStatus.RESCHEDULED: set(),
    ScheduleStatus.CANCELLED: set(),
    ScheduleStatus.PENDING_APPROVAL: {
        ScheduleStatus.SCHEDULED,
        ScheduleStatus.CANCELLED,
    },
}

SESSION_STATUS_FOR_SCHEDULE = {
    ScheduleStatus.DRAFT: SessionStatus.SCHEDULED,
    ScheduleStatus.SCHEDULED: SessionStatus.SCHEDULED,
    ScheduleStatus.CONFIRMED: SessionStatus.CONFIRMED,
    ScheduleStatus.ACTIVE: SessionStatus.ACTIVE,
    ScheduleStatus.COMPLETED: SessionStatus.COMPLETED,
    ScheduleStatus.RESCHEDULED: SessionStatus.RESCHEDULED,
    ScheduleStatus.CANCELLED: SessionStatus.CANCELLED,
    ScheduleStatus.PENDING_APPROVAL: SessionStatus.SCHEDULED,
    ScheduleStatus.SUSPENDED: SessionStatus.SUSPENDED,
}
