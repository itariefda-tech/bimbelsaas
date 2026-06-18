from enum import StrEnum


class BetaOnboardingStatus(StrEnum):
    INVITED = "invited"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"


class BetaFeedbackStatus(StrEnum):
    OPEN = "open"
    TRIAGED = "triaged"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class BetaFeedbackSeverity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


BETA_ONBOARDING_TRANSITIONS = {
    BetaOnboardingStatus.INVITED: {
        BetaOnboardingStatus.ACTIVE,
        BetaOnboardingStatus.PAUSED,
    },
    BetaOnboardingStatus.ACTIVE: {
        BetaOnboardingStatus.PAUSED,
        BetaOnboardingStatus.COMPLETED,
    },
    BetaOnboardingStatus.PAUSED: {
        BetaOnboardingStatus.ACTIVE,
        BetaOnboardingStatus.COMPLETED,
    },
    BetaOnboardingStatus.COMPLETED: set(),
}


BETA_FEEDBACK_TRANSITIONS = {
    BetaFeedbackStatus.OPEN: {
        BetaFeedbackStatus.TRIAGED,
        BetaFeedbackStatus.CLOSED,
    },
    BetaFeedbackStatus.TRIAGED: {
        BetaFeedbackStatus.IN_PROGRESS,
        BetaFeedbackStatus.RESOLVED,
        BetaFeedbackStatus.CLOSED,
    },
    BetaFeedbackStatus.IN_PROGRESS: {
        BetaFeedbackStatus.RESOLVED,
        BetaFeedbackStatus.CLOSED,
    },
    BetaFeedbackStatus.RESOLVED: {
        BetaFeedbackStatus.CLOSED,
    },
    BetaFeedbackStatus.CLOSED: set(),
}
