from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select

from app.domain.financial_status import AddonStatus, SubscriptionStatus
from app.extensions import db
from app.models.addon import StudentAddon, StudentBranchAccess
from app.models.subscription import AcademySubscription, SaasPlan


class EntitlementService:
    BASIC_FEATURES = frozenset(
        {"schedules", "attendance", "class_management", "invoicing", "parent_dashboard"}
    )

    def academy_has_feature(self, academy_id: UUID, feature_key: str) -> bool:
        if feature_key in self.BASIC_FEATURES:
            return True
        row = db.session.execute(
            select(AcademySubscription, SaasPlan)
            .join(SaasPlan, SaasPlan.id == AcademySubscription.plan_id)
            .where(AcademySubscription.academy_id == academy_id)
        ).first()
        if row is None:
            return False
        subscription, plan = row
        if subscription.status not in {
            SubscriptionStatus.TRIAL,
            SubscriptionStatus.ACTIVE,
            SubscriptionStatus.GRACE_PERIOD,
        }:
            return False
        return feature_key in set(plan.features or [])

    def student_has_feature(self, student_id: UUID, feature_key: str) -> bool:
        now = datetime.now(timezone.utc)
        return (
            db.session.scalar(
                select(StudentAddon.id).where(
                    StudentAddon.student_id == student_id,
                    StudentAddon.feature_key == feature_key,
                    StudentAddon.status == AddonStatus.ACTIVE,
                    StudentAddon.starts_at <= now,
                    (StudentAddon.ends_at.is_(None)) | (StudentAddon.ends_at > now),
                )
            )
            is not None
        )

    def student_can_access_branch(self, student_id: UUID, branch_id: UUID) -> bool:
        return (
            db.session.scalar(
                select(StudentBranchAccess.id)
                .join(StudentAddon, StudentAddon.id == StudentBranchAccess.student_addon_id)
                .where(
                    StudentBranchAccess.student_id == student_id,
                    StudentBranchAccess.branch_id == branch_id,
                    StudentBranchAccess.status == "active",
                    StudentAddon.status == AddonStatus.ACTIVE,
                    StudentAddon.feature_key == "cross_branch_student_access",
                )
            )
            is not None
        )
