from enum import StrEnum


class AttendanceStatus(StrEnum):
    PRESENT = "present"
    LATE = "late"
    ABSENT = "absent"
    EXCUSED = "excused"
    ONLINE = "online"


class AttendanceSheetStatus(StrEnum):
    DRAFT = "draft"
    FINALIZED = "finalized"


class AttendanceEditRequestStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
