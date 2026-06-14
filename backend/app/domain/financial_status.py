from enum import StrEnum


class InvoiceStatus(StrEnum):
    DRAFT = "draft"
    ISSUED = "issued"
    PENDING_PAYMENT = "pending_payment"
    PARTIALLY_PAID = "partially_paid"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"


class PaymentStatus(StrEnum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"


class SubscriptionStatus(StrEnum):
    TRIAL = "trial"
    ACTIVE = "active"
    GRACE_PERIOD = "grace_period"
    SUSPENDED = "suspended"
    ARCHIVED = "archived"


class AddonStatus(StrEnum):
    ACTIVE = "active"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class DeliveryStatus(StrEnum):
    QUEUED = "queued"
    DELIVERED = "delivered"
    FAILED = "failed"
