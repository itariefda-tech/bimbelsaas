from enum import StrEnum


class AcademyStatus(StrEnum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    ARCHIVED = "archived"


class BranchStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"
    SUSPENDED = "suspended"
    ARCHIVED = "archived"


ACADEMY_STATUS_TRANSITIONS: dict[AcademyStatus, frozenset[AcademyStatus]] = {
    AcademyStatus.ACTIVE: frozenset(
        {AcademyStatus.SUSPENDED, AcademyStatus.ARCHIVED}
    ),
    AcademyStatus.SUSPENDED: frozenset(
        {AcademyStatus.ACTIVE, AcademyStatus.ARCHIVED}
    ),
    AcademyStatus.ARCHIVED: frozenset(),
}

BRANCH_STATUS_TRANSITIONS: dict[BranchStatus, frozenset[BranchStatus]] = {
    BranchStatus.ACTIVE: frozenset(
        {
            BranchStatus.INACTIVE,
            BranchStatus.MAINTENANCE,
            BranchStatus.SUSPENDED,
            BranchStatus.ARCHIVED,
        }
    ),
    BranchStatus.INACTIVE: frozenset(
        {
            BranchStatus.ACTIVE,
            BranchStatus.MAINTENANCE,
            BranchStatus.SUSPENDED,
            BranchStatus.ARCHIVED,
        }
    ),
    BranchStatus.MAINTENANCE: frozenset(
        {
            BranchStatus.ACTIVE,
            BranchStatus.INACTIVE,
            BranchStatus.SUSPENDED,
            BranchStatus.ARCHIVED,
        }
    ),
    BranchStatus.SUSPENDED: frozenset(
        {
            BranchStatus.ACTIVE,
            BranchStatus.INACTIVE,
            BranchStatus.ARCHIVED,
        }
    ),
    BranchStatus.ARCHIVED: frozenset(),
}
