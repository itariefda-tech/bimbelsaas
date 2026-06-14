from datetime import date, datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import Date, DateTime, ForeignKeyConstraint, Index, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.extensions import db


class AcademicInvoice(db.Model):
    __tablename__ = "academic_invoices"
    __table_args__ = (
        UniqueConstraint("academy_id", "invoice_number", name="uq_invoices_academy_number"),
        UniqueConstraint("id", "academy_id", "branch_id", name="uq_invoices_id_scope"),
        ForeignKeyConstraint(
            ["branch_id", "academy_id"],
            ["branches.id", "branches.academy_id"],
            name="fk_invoices_branch_academy",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["student_id", "academy_id"],
            ["students.id", "students.academy_id"],
            name="fk_invoices_student_academy",
            ondelete="RESTRICT",
        ),
        Index("ix_invoices_student_status", "academy_id", "student_id", "status"),
        Index("ix_invoices_branch_due", "academy_id", "branch_id", "due_date"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    academy_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    branch_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    student_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    invoice_number: Mapped[str] = mapped_column(String(80), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="IDR")
    amount_minor: Mapped[int] = mapped_column(nullable=False)
    paid_minor: Mapped[int] = mapped_column(nullable=False, default=0)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="draft")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    issued_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
