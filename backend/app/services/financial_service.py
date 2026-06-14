from datetime import date, datetime, timezone
from uuid import UUID

from sqlalchemy import func, select

from app.common.errors import AuthorizationError, ConflictError, NotFoundError, ValidationError
from app.domain.financial_status import InvoiceStatus, PaymentStatus
from app.extensions import db
from app.models.academic_invoice import AcademicInvoice
from app.models.academic_payment import AcademicPayment
from app.models.parent import Parent
from app.models.parent_student import ParentStudent
from app.models.student import Student
from app.permissions.constants import Permission
from app.permissions.context import AuthorizationTarget, Principal
from app.services.audit_log_service import AuditEvent, AuditLogService
from app.services.authorization_service import AuthorizationService
from app.services.notification_service import NotificationService
from app.services.realtime_service import RealtimeService


class FinancialService:
    def create_invoice(
        self,
        principal: Principal,
        *,
        academy_id: UUID,
        branch_id: UUID,
        student_id: UUID,
        invoice_number: str,
        description: str,
        amount_minor: int,
        due_date: date,
        notes: str | None = None,
    ) -> AcademicInvoice:
        student = db.session.get(Student, student_id)
        if student is None or student.academy_id != academy_id:
            raise NotFoundError("Student")
        if student.home_branch_id != branch_id:
            raise ValidationError("Invoice branch must match the student's home branch.")
        target = AuthorizationTarget(academy_id=academy_id, branch_id=branch_id, student_id=student_id)
        AuthorizationService.require(principal, Permission.INVOICE_CREATE, target)
        if amount_minor <= 0:
            raise ValidationError("amount_minor must be positive.")
        invoice = AcademicInvoice(
            academy_id=academy_id,
            branch_id=branch_id,
            student_id=student_id,
            invoice_number=invoice_number,
            description=description,
            amount_minor=amount_minor,
            due_date=due_date,
            notes=notes,
            created_by=principal.user.id,
        )
        db.session.add(invoice)
        db.session.flush()
        self._audit(principal, invoice, "invoice.created")
        db.session.commit()
        return invoice

    def issue(self, principal: Principal, invoice_id: UUID) -> AcademicInvoice:
        invoice = self._invoice(invoice_id)
        AuthorizationService.require(principal, Permission.INVOICE_EDIT, self._target(invoice))
        if invoice.status != InvoiceStatus.DRAFT:
            raise ConflictError("Only draft invoices can be issued.")
        invoice.status = InvoiceStatus.ISSUED
        invoice.issued_at = datetime.now(timezone.utc)
        self._notify_parents(invoice, "invoice.issued", "New invoice issued", "high")
        self._event(invoice, "invoice.issued")
        self._audit(principal, invoice, "invoice.issued")
        db.session.commit()
        return invoice

    def cancel(self, principal: Principal, invoice_id: UUID, reason: str) -> AcademicInvoice:
        invoice = self._invoice(invoice_id)
        AuthorizationService.require(principal, Permission.INVOICE_EDIT, self._target(invoice))
        if invoice.status in {InvoiceStatus.PAID, InvoiceStatus.CANCELLED}:
            raise ConflictError("Paid or cancelled invoices cannot be cancelled here.")
        invoice.status = InvoiceStatus.CANCELLED
        invoice.cancelled_at = datetime.now(timezone.utc)
        self._audit(principal, invoice, "invoice.cancelled", reason)
        self._notify_parents(invoice, "invoice.cancelled", "Invoice cancelled", "high")
        self._event(invoice, "invoice.cancelled")
        db.session.commit()
        return invoice

    def submit_payment(
        self,
        principal: Principal,
        invoice_id: UUID,
        *,
        reference_number: str,
        amount_minor: int,
        method: str,
        proof: dict[str, str],
    ) -> AcademicPayment:
        invoice = self._invoice(invoice_id)
        self._require_parent_invoice(principal, invoice)
        if invoice.status in {InvoiceStatus.DRAFT, InvoiceStatus.CANCELLED, InvoiceStatus.PAID}:
            raise ConflictError("This invoice cannot accept a payment.")
        if amount_minor <= 0 or amount_minor > invoice.amount_minor - invoice.paid_minor:
            raise ValidationError("Payment amount exceeds the outstanding invoice balance.")
        required = {"storage_key", "file_name", "mime_type", "checksum_sha256"}
        if required - proof.keys() or len(proof["checksum_sha256"]) != 64:
            raise ValidationError("Complete payment proof metadata is required.")
        payment = AcademicPayment(
            academy_id=invoice.academy_id,
            branch_id=invoice.branch_id,
            invoice_id=invoice.id,
            reference_number=reference_number,
            amount_minor=amount_minor,
            method=method,
            proof_storage_key=proof["storage_key"],
            proof_file_name=proof["file_name"],
            proof_mime_type=proof["mime_type"],
            proof_checksum_sha256=proof["checksum_sha256"].lower(),
            submitted_by=principal.user.id,
        )
        db.session.add(payment)
        invoice.status = InvoiceStatus.PENDING_PAYMENT
        self._audit(principal, invoice, "payment.proof_submitted")
        db.session.commit()
        return payment

    def decide_payment(
        self,
        principal: Principal,
        payment_id: UUID,
        *,
        approve: bool,
        reason: str | None = None,
    ) -> AcademicPayment:
        payment = db.session.get(AcademicPayment, payment_id)
        if payment is None:
            raise NotFoundError("Payment")
        invoice = self._invoice(payment.invoice_id)
        AuthorizationService.require(principal, Permission.PAYMENT_CONFIRM, self._target(invoice))
        if payment.status != PaymentStatus.PENDING:
            raise ConflictError("Payment has already been decided.")
        if not approve and not reason:
            raise ValidationError("A rejection reason is required.")
        payment.status = PaymentStatus.CONFIRMED if approve else PaymentStatus.REJECTED
        payment.confirmed_by = principal.user.id
        payment.confirmed_at = datetime.now(timezone.utc)
        payment.rejection_reason = None if approve else reason
        if approve:
            invoice.paid_minor += payment.amount_minor
        self._sync_invoice_status(invoice)
        action = "payment.confirmed" if approve else "payment.rejected"
        self._audit(principal, invoice, action, reason)
        self._notify_parents(invoice, action, "Payment updated", "high" if not approve else "medium")
        self._event(invoice, action)
        db.session.commit()
        return payment

    def list_parent_invoices(self, principal: Principal, academy_id: UUID) -> list[dict]:
        parent = db.session.scalar(
            select(Parent).where(Parent.academy_id == academy_id, Parent.user_id == principal.user.id)
        )
        if parent is None:
            raise AuthorizationError()
        invoices = list(
            db.session.scalars(
                select(AcademicInvoice)
                .join(ParentStudent, ParentStudent.student_id == AcademicInvoice.student_id)
                .where(
                    AcademicInvoice.academy_id == academy_id,
                    ParentStudent.parent_id == parent.id,
                    ParentStudent.relationship_status == "active",
                    AcademicInvoice.status != InvoiceStatus.DRAFT,
                )
                .order_by(AcademicInvoice.due_date.desc(), AcademicInvoice.id)
            )
        )
        return [self.serialize_invoice(item, include_payments=True) for item in invoices]

    def get_invoice(self, principal: Principal, invoice_id: UUID) -> dict:
        invoice = self._invoice(invoice_id)
        if not AuthorizationService.is_allowed(principal, Permission.INVOICE_VIEW, self._target(invoice)):
            self._require_parent_invoice(principal, invoice)
        return self.serialize_invoice(invoice, include_payments=True)

    @staticmethod
    def serialize_invoice(invoice: AcademicInvoice, *, include_payments: bool = False) -> dict:
        data = {
            "id": str(invoice.id),
            "academy_id": str(invoice.academy_id),
            "branch_id": str(invoice.branch_id),
            "student_id": str(invoice.student_id),
            "invoice_number": invoice.invoice_number,
            "description": invoice.description,
            "currency": invoice.currency,
            "amount_minor": invoice.amount_minor,
            "paid_minor": invoice.paid_minor,
            "outstanding_minor": invoice.amount_minor - invoice.paid_minor,
            "due_date": invoice.due_date.isoformat(),
            "status": invoice.status,
            "issued_at": invoice.issued_at.isoformat() if invoice.issued_at else None,
        }
        if include_payments:
            payments = list(
                db.session.scalars(
                    select(AcademicPayment)
                    .where(AcademicPayment.invoice_id == invoice.id)
                    .order_by(AcademicPayment.submitted_at.desc())
                )
            )
            data["payments"] = [FinancialService.serialize_payment(item) for item in payments]
        return data

    @staticmethod
    def serialize_payment(payment: AcademicPayment) -> dict:
        return {
            "id": str(payment.id),
            "reference_number": payment.reference_number,
            "amount_minor": payment.amount_minor,
            "method": payment.method,
            "status": payment.status,
            "proof": {
                "file_name": payment.proof_file_name,
                "mime_type": payment.proof_mime_type,
                "checksum_sha256": payment.proof_checksum_sha256,
            },
            "submitted_at": payment.submitted_at.isoformat(),
            "confirmed_at": payment.confirmed_at.isoformat() if payment.confirmed_at else None,
            "rejection_reason": payment.rejection_reason,
        }

    def mark_overdue(self, today: date | None = None) -> int:
        today = today or date.today()
        invoices = list(
            db.session.scalars(
                select(AcademicInvoice).where(
                    AcademicInvoice.due_date < today,
                    AcademicInvoice.status.in_(
                        (InvoiceStatus.ISSUED, InvoiceStatus.PENDING_PAYMENT, InvoiceStatus.PARTIALLY_PAID)
                    ),
                )
            )
        )
        for invoice in invoices:
            invoice.status = InvoiceStatus.OVERDUE
            self._notify_parents(invoice, "invoice.overdue", "Invoice overdue", "high")
        db.session.commit()
        return len(invoices)

    def _require_parent_invoice(self, principal: Principal, invoice: AcademicInvoice) -> None:
        linked = db.session.scalar(
            select(ParentStudent.id)
            .join(Parent, Parent.id == ParentStudent.parent_id)
            .where(
                Parent.user_id == principal.user.id,
                ParentStudent.academy_id == invoice.academy_id,
                ParentStudent.student_id == invoice.student_id,
                ParentStudent.relationship_status == "active",
            )
        )
        if linked is None:
            raise AuthorizationError()

    @staticmethod
    def _invoice(invoice_id: UUID) -> AcademicInvoice:
        invoice = db.session.get(AcademicInvoice, invoice_id)
        if invoice is None:
            raise NotFoundError("Invoice")
        return invoice

    @staticmethod
    def _target(invoice: AcademicInvoice) -> AuthorizationTarget:
        return AuthorizationTarget(
            academy_id=invoice.academy_id,
            branch_id=invoice.branch_id,
            student_id=invoice.student_id,
        )

    @staticmethod
    def _sync_invoice_status(invoice: AcademicInvoice) -> None:
        if invoice.paid_minor >= invoice.amount_minor:
            invoice.status = InvoiceStatus.PAID
        elif invoice.paid_minor > 0:
            invoice.status = InvoiceStatus.PARTIALLY_PAID
        else:
            invoice.status = InvoiceStatus.ISSUED

    def _notify_parents(self, invoice, event_type, title, priority):
        user_ids = list(
            db.session.scalars(
                select(Parent.user_id)
                .join(ParentStudent, ParentStudent.parent_id == Parent.id)
                .where(
                    ParentStudent.student_id == invoice.student_id,
                    ParentStudent.relationship_status == "active",
                    Parent.status == "active",
                )
            )
        )
        for user_id in user_ids:
            NotificationService().emit(
                academy_id=invoice.academy_id,
                recipient_user_id=user_id,
                notification_type=event_type,
                priority=priority,
                title=title,
                payload={"invoice_id": str(invoice.id), "student_id": str(invoice.student_id)},
                dedup_key=f"{event_type}:{invoice.id}:{invoice.paid_minor}",
            )

    @staticmethod
    def _event(invoice, event_type):
        RealtimeService().enqueue(
            academy_id=invoice.academy_id,
            branch_id=invoice.branch_id,
            event_type=event_type,
            payload={"invoice_id": str(invoice.id), "student_id": str(invoice.student_id), "status": invoice.status},
            dedup_key=f"{event_type}:{invoice.id}:{invoice.updated_at.isoformat()}",
            room=f"student:{invoice.student_id}",
        )

    @staticmethod
    def _audit(principal, invoice, action, reason=None):
        AuditLogService().record(
            AuditEvent(
                entity_type="academic_invoice",
                entity_id=str(invoice.id),
                action_type=action,
                academy_id=invoice.academy_id,
                branch_id=invoice.branch_id,
                actor_user_id=principal.user.id,
                new_data=FinancialService.serialize_invoice(invoice),
                reason=reason,
            )
        )
