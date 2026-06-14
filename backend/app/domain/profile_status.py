from enum import StrEnum


class ProfileStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class TeacherBranchStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ENDED = "ended"
