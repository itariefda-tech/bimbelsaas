from enum import StrEnum


class LessonSummaryStatus(StrEnum):
    DRAFT = "draft"
    PUBLISHED = "published"


class LessonSummaryEditRequestStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
