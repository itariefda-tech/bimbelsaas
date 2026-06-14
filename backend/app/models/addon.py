from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, ForeignKeyConstraint, Index, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.extensions import db


class AddonDefinition(db.Model):
    __tablename__ = "addon_definitions"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    code: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    feature_key: Mapped[str] = mapped_column(String(100), nullable=False)
    price_minor: Mapped[int] = mapped_column(nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="IDR")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class StudentAddon(db.Model):
    __tablename__ = "student_addons"
    __table_args__ = (
        ForeignKeyConstraint(
            ["student_id", "academy_id"],
            ["students.id", "students.academy_id"],
            name="fk_student_addons_student_academy",
            ondelete="CASCADE",
        ),
        Index("ix_student_addons_feature_status", "student_id", "feature_key", "status"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    academy_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    student_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    addon_id: Mapped[UUID] = mapped_column(
        ForeignKey("addon_definitions.id", ondelete="RESTRICT"), nullable=False
    )
    feature_key: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="active")
    purchased_by: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class StudentBranchAccess(db.Model):
    __tablename__ = "student_branch_access"
    __table_args__ = (
        UniqueConstraint("student_id", "branch_id", name="uq_student_branch_access"),
        ForeignKeyConstraint(
            ["student_id", "academy_id"],
            ["students.id", "students.academy_id"],
            name="fk_student_branch_access_student_academy",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["branch_id", "academy_id"],
            ["branches.id", "branches.academy_id"],
            name="fk_student_branch_access_branch_academy",
            ondelete="CASCADE",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    academy_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    student_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    branch_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    student_addon_id: Mapped[UUID] = mapped_column(
        ForeignKey("student_addons.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="active")
    granted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
