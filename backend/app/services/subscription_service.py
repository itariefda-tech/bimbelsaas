from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select

from app.common.errors import AuthorizationError, ConflictError, NotFoundError, ValidationError
from app.domain.financial_status import AddonStatus, SubscriptionStatus
from app.extensions import db
from app.models.addon import AddonDefinition, StudentAddon, StudentBranchAccess
from app.models.branch import Branch
from app.models.parent import Parent
from app.models.parent_student import ParentStudent
from app.models.student import Student
from app.models.subscription import AcademySubscription, SaasPlan
from app.permissions.constants import Permission
from app.permissions.context import AuthorizationTarget, Principal
from app.services.audit_log_service import AuditEvent, AuditLogService
from app.services.authorization_service import AuthorizationService


class SubscriptionService:
    TRANSITIONS = {
        SubscriptionStatus.TRIAL: {SubscriptionStatus.ACTIVE, SubscriptionStatus.GRACE_PERIOD, SubscriptionStatus.SUSPENDED},
        SubscriptionStatus.ACTIVE: {SubscriptionStatus.GRACE_PERIOD, SubscriptionStatus.SUSPENDED},
        SubscriptionStatus.GRACE_PERIOD: {SubscriptionStatus.ACTIVE, SubscriptionStatus.SUSPENDED},
        SubscriptionStatus.SUSPENDED: {SubscriptionStatus.ACTIVE, SubscriptionStatus.ARCHIVED},
        SubscriptionStatus.ARCHIVED: set(),
    }

    def create_plan(self, principal, *, code, name, price_minor, features) -> SaasPlan:
        AuthorizationService.require(principal, Permission.SUBSCRIPTION_MANAGE, AuthorizationTarget())
        if price_minor < 0 or not isinstance(features, list):
            raise ValidationError("Invalid plan price or features.")
        plan = SaasPlan(code=code, name=name, price_minor=price_minor, features=features)
        db.session.add(plan)
        db.session.commit()
        return plan

    def activate(self, principal, *, academy_id, plan_id, status, period_end) -> AcademySubscription:
        AuthorizationService.require(principal, Permission.SUBSCRIPTION_MANAGE, AuthorizationTarget(academy_id=academy_id))
        if db.session.get(SaasPlan, plan_id) is None:
            raise NotFoundError("SaaS plan")
        if db.session.scalar(select(AcademySubscription).where(AcademySubscription.academy_id == academy_id)):
            raise ConflictError("Academy already has a subscription.")
        now = datetime.now(timezone.utc)
        subscription = AcademySubscription(
            academy_id=academy_id,
            plan_id=plan_id,
            status=SubscriptionStatus(status),
            current_period_start=now,
            current_period_end=period_end,
            created_by=principal.user.id,
        )
        db.session.add(subscription)
        self._audit(principal, subscription, "subscription.activated")
        db.session.commit()
        return subscription

    def transition(self, principal, subscription_id, target_status, grace_days=7):
        subscription = db.session.get(AcademySubscription, subscription_id)
        if subscription is None:
            raise NotFoundError("Subscription")
        AuthorizationService.require(
            principal, Permission.SUBSCRIPTION_MANAGE, AuthorizationTarget(academy_id=subscription.academy_id)
        )
        current = SubscriptionStatus(subscription.status)
        target = SubscriptionStatus(target_status)
        if target not in self.TRANSITIONS[current]:
            raise ConflictError(f"Cannot transition subscription from {current} to {target}.")
        if target == SubscriptionStatus.GRACE_PERIOD:
            if grace_days < 7 or grace_days > 14:
                raise ValidationError("grace_days must be between 7 and 14.")
            subscription.grace_period_end = datetime.now(timezone.utc) + timedelta(days=grace_days)
        else:
            subscription.grace_period_end = None
        subscription.status = target
        self._audit(principal, subscription, "subscription.status_changed")
        db.session.commit()
        return subscription

    def reconcile_expired(self, now: datetime | None = None) -> dict[str, int]:
        now = now or datetime.now(timezone.utc)
        entered_grace = suspended = 0
        for subscription in db.session.scalars(
            select(AcademySubscription).where(
                AcademySubscription.status.in_(
                    (SubscriptionStatus.TRIAL, SubscriptionStatus.ACTIVE)
                ),
                AcademySubscription.current_period_end <= now,
            )
        ):
            subscription.status = SubscriptionStatus.GRACE_PERIOD
            subscription.grace_period_end = now + timedelta(days=7)
            entered_grace += 1
        for subscription in db.session.scalars(
            select(AcademySubscription).where(
                AcademySubscription.status == SubscriptionStatus.GRACE_PERIOD,
                AcademySubscription.grace_period_end <= now,
            )
        ):
            subscription.status = SubscriptionStatus.SUSPENDED
            subscription.grace_period_end = None
            suspended += 1
        db.session.commit()
        return {"entered_grace": entered_grace, "suspended": suspended}

    def view(self, principal, academy_id):
        AuthorizationService.require(
            principal, Permission.SUBSCRIPTION_VIEW, AuthorizationTarget(academy_id=academy_id)
        )
        subscription = db.session.scalar(
            select(AcademySubscription).where(AcademySubscription.academy_id == academy_id)
        )
        if subscription is None:
            raise NotFoundError("Subscription")
        return self.serialize_subscription(subscription)

    def create_addon(self, principal, *, code, name, feature_key, price_minor):
        AuthorizationService.require(principal, Permission.SUBSCRIPTION_MANAGE, AuthorizationTarget())
        addon = AddonDefinition(
            code=code, name=name, feature_key=feature_key, price_minor=price_minor
        )
        db.session.add(addon)
        db.session.commit()
        return addon

    def buy_addon(self, principal, *, student_id, addon_id, branch_ids, ends_at=None):
        student = db.session.get(Student, student_id)
        addon = db.session.get(AddonDefinition, addon_id)
        if student is None or addon is None or not addon.is_active:
            raise NotFoundError("Student or addon")
        AuthorizationService.require(
            principal,
            Permission.ADDON_BUY,
            AuthorizationTarget(
                academy_id=student.academy_id,
                branch_id=student.home_branch_id,
                student_id=student.id,
            ),
        )
        self._require_parent_link(principal, student)
        purchase = StudentAddon(
            academy_id=student.academy_id,
            student_id=student.id,
            addon_id=addon.id,
            feature_key=addon.feature_key,
            purchased_by=principal.user.id,
            starts_at=datetime.now(timezone.utc),
            ends_at=ends_at,
        )
        db.session.add(purchase)
        db.session.flush()
        if addon.feature_key == "cross_branch_student_access":
            if not branch_ids:
                raise ValidationError("At least one target branch is required.")
            for branch_id in set(branch_ids):
                branch = db.session.get(Branch, branch_id)
                if branch is None or branch.academy_id != student.academy_id:
                    raise ValidationError("Addon branch must belong to the student's academy.")
                if branch_id == student.home_branch_id:
                    continue
                db.session.add(
                    StudentBranchAccess(
                        academy_id=student.academy_id,
                        student_id=student.id,
                        branch_id=branch_id,
                        student_addon_id=purchase.id,
                    )
                )
        self._audit(principal, purchase, "addon.purchased")
        db.session.commit()
        return purchase

    def cancel_addon(self, principal, purchase_id):
        purchase = db.session.get(StudentAddon, purchase_id)
        if purchase is None:
            raise NotFoundError("Student addon")
        student = db.session.get(Student, purchase.student_id)
        self._require_parent_link(principal, student)
        if purchase.status != AddonStatus.ACTIVE:
            raise ConflictError("Addon is not active.")
        purchase.status = AddonStatus.CANCELLED
        purchase.cancelled_at = datetime.now(timezone.utc)
        for access in db.session.scalars(
            select(StudentBranchAccess).where(StudentBranchAccess.student_addon_id == purchase.id)
        ):
            access.status = "cancelled"
        self._audit(principal, purchase, "addon.cancelled")
        db.session.commit()
        return purchase

    @staticmethod
    def serialize_subscription(item):
        return {
            "id": str(item.id),
            "academy_id": str(item.academy_id),
            "plan_id": str(item.plan_id),
            "status": item.status,
            "current_period_start": item.current_period_start.isoformat(),
            "current_period_end": item.current_period_end.isoformat(),
            "grace_period_end": item.grace_period_end.isoformat() if item.grace_period_end else None,
        }

    @staticmethod
    def serialize_addon(item):
        return {
            "id": str(item.id),
            "student_id": str(item.student_id),
            "addon_id": str(item.addon_id),
            "feature_key": item.feature_key,
            "status": item.status,
            "starts_at": item.starts_at.isoformat(),
            "ends_at": item.ends_at.isoformat() if item.ends_at else None,
        }

    @staticmethod
    def _require_parent_link(principal, student):
        linked = db.session.scalar(
            select(ParentStudent.id)
            .join(Parent, Parent.id == ParentStudent.parent_id)
            .where(
                Parent.user_id == principal.user.id,
                ParentStudent.student_id == student.id,
                ParentStudent.relationship_status == "active",
            )
        )
        if linked is None:
            raise AuthorizationError()

    @staticmethod
    def _audit(principal, entity, action):
        AuditLogService().record(
            AuditEvent(
                entity_type=entity.__tablename__,
                entity_id=str(entity.id),
                action_type=action,
                academy_id=getattr(entity, "academy_id", None),
                actor_user_id=principal.user.id,
            )
        )
