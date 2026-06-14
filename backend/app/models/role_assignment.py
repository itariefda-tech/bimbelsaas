from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import (
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    String,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db


class RoleAssignment(db.Model):
    __tablename__ = "role_assignments"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "role",
            "scope_key",
            name="uq_role_assignments_identity_scope",
        ),
        Index(
            "ix_role_assignments_user_status",
            "user_id",
            "status",
        ),
        Index(
            "ix_role_assignments_academy_branch",
            "academy_id",
            "branch_id",
        ),
        ForeignKeyConstraint(
            ["branch_id", "academy_id"],
            ["branches.id", "branches.academy_id"],
            name="fk_role_assignments_branch_academy_branches",
            ondelete="RESTRICT",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    role: Mapped[str] = mapped_column(String(50), nullable=False)
    scope_type: Mapped[str] = mapped_column(String(50), nullable=False)
    scope_key: Mapped[str] = mapped_column(String(150), nullable=False)
    academy_id: Mapped[UUID | None] = mapped_column(
        ForeignKey(
            "academies.id",
            name="fk_role_assignments_academy_id_academies",
            ondelete="RESTRICT",
        ),
        nullable=True,
    )
    branch_id: Mapped[UUID | None] = mapped_column(Uuid, nullable=True)
    scope_id: Mapped[UUID | None] = mapped_column(Uuid, nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="active")
    assigned_by: Mapped[UUID | None] = mapped_column(Uuid, nullable=True)
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    user = relationship("User", back_populates="role_assignments")
