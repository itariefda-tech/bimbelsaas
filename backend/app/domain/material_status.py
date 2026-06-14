from enum import StrEnum


class MaterialStatus(StrEnum):
    ACTIVE = "active"
    ARCHIVED = "archived"


class MaterialVersionStatus(StrEnum):
    DRAFT = "draft"
    REVIEW = "review"
    READY = "ready"
    ARCHIVED = "archived"


class MaterialDistributionStatus(StrEnum):
    READY = "ready"
    UPDATED = "updated"
    ARCHIVED = "archived"


class NotificationPriority(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
