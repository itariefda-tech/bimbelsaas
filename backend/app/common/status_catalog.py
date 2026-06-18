from typing import Any


STATUS_CATALOG: dict[str, dict[str, dict[str, str]]] = {
    "attendance": {
        "present": {"label": "Present", "tone": "success"},
        "late": {"label": "Late", "tone": "warning"},
        "absent": {"label": "Absent", "tone": "danger"},
        "excused": {"label": "Excused", "tone": "neutral"},
        "online": {"label": "Online", "tone": "info"},
    },
    "attendance_sheet": {
        "draft": {"label": "Draft", "tone": "neutral"},
        "finalized": {"label": "Finalized", "tone": "success"},
    },
    "invoice": {
        "draft": {"label": "Draft", "tone": "neutral"},
        "issued": {"label": "Issued", "tone": "info"},
        "pending_payment": {"label": "Pending payment", "tone": "warning"},
        "partially_paid": {"label": "Partially paid", "tone": "warning"},
        "paid": {"label": "Paid", "tone": "success"},
        "overdue": {"label": "Overdue", "tone": "danger"},
        "cancelled": {"label": "Cancelled", "tone": "muted"},
    },
    "payment": {
        "pending": {"label": "Pending", "tone": "warning"},
        "confirmed": {"label": "Confirmed", "tone": "success"},
        "rejected": {"label": "Rejected", "tone": "danger"},
    },
    "schedule": {
        "draft": {"label": "Draft", "tone": "neutral"},
        "scheduled": {"label": "Scheduled", "tone": "info"},
        "confirmed": {"label": "Confirmed", "tone": "success"},
        "active": {"label": "Active", "tone": "success"},
        "completed": {"label": "Completed", "tone": "success"},
        "rescheduled": {"label": "Rescheduled", "tone": "warning"},
        "cancelled": {"label": "Cancelled", "tone": "muted"},
        "pending_approval": {"label": "Pending approval", "tone": "warning"},
        "suspended": {"label": "Suspended", "tone": "danger"},
    },
    "subscription": {
        "trial": {"label": "Trial", "tone": "info"},
        "active": {"label": "Active", "tone": "success"},
        "grace_period": {"label": "Grace period", "tone": "warning"},
        "suspended": {"label": "Suspended", "tone": "danger"},
        "archived": {"label": "Archived", "tone": "muted"},
    },
}


def status_meta(*groups: str) -> dict[str, Any]:
    selected = groups or tuple(STATUS_CATALOG)
    return {
        "status_catalog": {
            group: STATUS_CATALOG[group]
            for group in selected
            if group in STATUS_CATALOG
        }
    }
