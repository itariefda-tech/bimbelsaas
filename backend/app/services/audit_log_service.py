from dataclasses import dataclass
from typing import Any
from uuid import UUID

from app.extensions import db
from app.models.audit_log import AuditLog
from app.repositories.audit_log_repository import AuditLogRepository


@dataclass(frozen=True)
class AuditEvent:
    entity_type: str
    entity_id: str
    action_type: str
    academy_id: UUID | None = None
    branch_id: UUID | None = None
    actor_user_id: UUID | None = None
    previous_data: dict[str, Any] | None = None
    new_data: dict[str, Any] | None = None
    reason: str | None = None
    ip_address: str | None = None
    request_id: str | None = None


class AuditLogService:
    def __init__(self, repository: AuditLogRepository | None = None) -> None:
        self.repository = repository or AuditLogRepository()

    def record(self, event: AuditEvent, *, commit: bool = False) -> AuditLog:
        audit_log = AuditLog(
            academy_id=event.academy_id,
            branch_id=event.branch_id,
            actor_user_id=event.actor_user_id,
            entity_type=event.entity_type,
            entity_id=event.entity_id,
            action_type=event.action_type,
            previous_data=event.previous_data,
            new_data=event.new_data,
            reason=event.reason,
            ip_address=event.ip_address,
            request_id=event.request_id,
        )
        self.repository.add(audit_log)
        if commit:
            db.session.commit()
        else:
            db.session.flush()
        return audit_log

