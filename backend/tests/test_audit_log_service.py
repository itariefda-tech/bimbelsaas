from app.models.audit_log import AuditLog
from app.services.audit_log_service import AuditEvent, AuditLogService


def test_audit_service_records_traceable_event(app):
    with app.app_context():
        audit_log = AuditLogService().record(
            AuditEvent(
                entity_type="system",
                entity_id="backend-foundation",
                action_type="initialized",
                new_data={"phase": 1},
                reason="Phase 1 foundation",
                request_id="test-request",
            )
        )

        stored = AuditLog.query.one()

        assert stored.id == audit_log.id
        assert stored.action_type == "initialized"
        assert stored.new_data == {"phase": 1}
        assert stored.reason == "Phase 1 foundation"

