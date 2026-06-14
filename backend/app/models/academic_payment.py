from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKeyConstraint, Index, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.extensions import db


class AcademicPayment(db.Model):
    __tablename__ = "academic_payments"
    __table_args__ = (
        UniqueConstraint("academy_id", "reference_number", name="uq_payments_academy_reference"),
        ForeignKeyConstraint(
            ["invoice_id", "academy_id", "branch_id"],
            ["academic_invoices.id", "academic_invoices.academy_id", "academic_invoices.branch_id"],
            name="fk_payments_invoice_scope",
            ondelete="CASCADE",
        ),
        Index("ix_payments_invoice_status", "invoice_id", "status"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    academy_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    branch_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    invoice_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    reference_number: Mapped[str] = mapped_column(String(100), nullable=False)
    amount_minor: Mapped[int] = mapped_column(nullable=False)
    method: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="pending")
    proof_storage_key: Mapped[str | None] = mapped_column(String(500), nullable=True)
    proof_file_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    proof_mime_type: Mapped[str | None] = mapped_column(String(150), nullable=True)
    proof_checksum_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    submitted_by: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    confirmed_by: Mapped[UUID | None] = mapped_column(Uuid, nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
