import re
from datetime import datetime, timezone
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.common.errors import ConflictError, NotFoundError, ValidationError
from app.domain.organization_status import (
    ACADEMY_STATUS_TRANSITIONS,
    AcademyStatus,
)
from app.extensions import db
from app.models.academy import Academy
from app.permissions.constants import Permission
from app.permissions.context import AuthorizationTarget, Principal
from app.repositories.academy_repository import AcademyRepository
from app.services.audit_log_service import AuditEvent, AuditLogService
from app.services.authorization_service import AuthorizationService

SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class AcademyService:
    def __init__(
        self,
        repository: AcademyRepository | None = None,
        audit_service: AuditLogService | None = None,
    ) -> None:
        self.repository = repository or AcademyRepository()
        self.audit = audit_service or AuditLogService()

    def list_visible(self, principal: Principal) -> list[Academy]:
        if AuthorizationService.is_allowed(
            principal,
            Permission.PLATFORM_MANAGE,
            AuthorizationTarget(),
        ):
            return self.repository.list_all()

        academy_ids = {
            assignment.academy_id
            for assignment in principal.assignments
            if assignment.academy_id is not None
        }
        return self.repository.list_by_ids(academy_ids)

    def get_visible(self, principal: Principal, academy_id: UUID) -> Academy:
        academy = self._get(academy_id)
        AuthorizationService.require(
            principal,
            Permission.ACADEMY_VIEW,
            AuthorizationTarget(academy_id=academy.id),
        )
        return academy

    def create(
        self,
        principal: Principal,
        *,
        name: str,
        slug: str,
        timezone_name: str,
        currency: str,
        logo_url: str | None = None,
    ) -> Academy:
        AuthorizationService.require(
            principal,
            Permission.ACADEMY_MANAGE,
            AuthorizationTarget(),
        )
        normalized_slug = self._validate_slug(slug)
        if self.repository.get_by_slug(normalized_slug) is not None:
            raise ConflictError(
                "An academy with this slug already exists.",
                "academy_slug_exists",
            )
        academy = Academy(
            name=self._required_name(name),
            slug=normalized_slug,
            timezone=self._validate_timezone(timezone_name),
            currency=self._validate_currency(currency),
            logo_url=self._optional_text(logo_url),
            created_by=principal.user.id,
            updated_by=principal.user.id,
        )
        self.repository.add(academy)
        db.session.flush()
        self._audit(principal, academy, "academy.created", new_data=self.serialize(academy))
        db.session.commit()
        return academy

    def update(
        self,
        principal: Principal,
        academy_id: UUID,
        changes: dict,
    ) -> Academy:
        academy = self._get(academy_id)
        AuthorizationService.require(
            principal,
            Permission.ACADEMY_MANAGE,
            AuthorizationTarget(academy_id=academy.id),
        )
        if academy.status == AcademyStatus.ARCHIVED:
            raise ConflictError("Archived academies cannot be edited.")

        previous = self.serialize(academy)
        if "name" in changes:
            academy.name = self._required_name(changes["name"])
        if "slug" in changes:
            slug = self._validate_slug(changes["slug"])
            existing = self.repository.get_by_slug(slug)
            if existing is not None and existing.id != academy.id:
                raise ConflictError(
                    "An academy with this slug already exists.",
                    "academy_slug_exists",
                )
            academy.slug = slug
        if "timezone" in changes:
            academy.timezone = self._validate_timezone(changes["timezone"])
        if "currency" in changes:
            academy.currency = self._validate_currency(changes["currency"])
        if "logo_url" in changes:
            academy.logo_url = self._optional_text(changes["logo_url"])
        if "status" in changes and changes["status"] != academy.status:
            AuthorizationService.require(
                principal,
                Permission.PLATFORM_MANAGE,
                AuthorizationTarget(),
            )
            self._transition_status(academy, changes["status"])

        academy.updated_by = principal.user.id
        self._audit(
            principal,
            academy,
            "academy.updated",
            previous_data=previous,
            new_data=self.serialize(academy),
        )
        db.session.commit()
        return academy

    def archive(self, principal: Principal, academy_id: UUID) -> Academy:
        academy = self._get(academy_id)
        AuthorizationService.require(
            principal,
            Permission.PLATFORM_MANAGE,
            AuthorizationTarget(),
        )
        if academy.status != AcademyStatus.ARCHIVED:
            previous = self.serialize(academy)
            self._transition_status(academy, AcademyStatus.ARCHIVED.value)
            academy.updated_by = principal.user.id
            self._audit(
                principal,
                academy,
                "academy.archived",
                previous_data=previous,
                new_data=self.serialize(academy),
            )
            db.session.commit()
        return academy

    def _get(self, academy_id: UUID) -> Academy:
        academy = self.repository.get_by_id(academy_id)
        if academy is None:
            raise NotFoundError("Academy")
        return academy

    @staticmethod
    def serialize(academy: Academy) -> dict[str, object]:
        return {
            "id": str(academy.id),
            "name": academy.name,
            "slug": academy.slug,
            "logo_url": academy.logo_url,
            "timezone": academy.timezone,
            "currency": academy.currency,
            "status": academy.status,
            "created_at": academy.created_at.isoformat(),
            "updated_at": academy.updated_at.isoformat(),
            "archived_at": (
                academy.archived_at.isoformat() if academy.archived_at else None
            ),
        }

    @staticmethod
    def _required_name(value: object) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValidationError("Academy name is required.")
        return value.strip()

    @staticmethod
    def _validate_slug(value: object) -> str:
        if not isinstance(value, str):
            raise ValidationError("Academy slug is required.")
        slug = value.strip().lower()
        if not SLUG_PATTERN.fullmatch(slug):
            raise ValidationError(
                "Academy slug must contain lowercase letters, numbers, and hyphens."
            )
        return slug

    @staticmethod
    def _validate_timezone(value: object) -> str:
        if not isinstance(value, str):
            raise ValidationError("Timezone is required.")
        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError as error:
            raise ValidationError("Timezone must be a valid IANA timezone.") from error
        return value

    @staticmethod
    def _validate_currency(value: object) -> str:
        if not isinstance(value, str) or len(value.strip()) != 3:
            raise ValidationError("Currency must be a 3-letter ISO code.")
        return value.strip().upper()

    @staticmethod
    def _optional_text(value: object) -> str | None:
        if value in (None, ""):
            return None
        if not isinstance(value, str):
            raise ValidationError("Optional text fields must be strings.")
        return value.strip()

    @staticmethod
    def _transition_status(academy: Academy, target_value: object) -> None:
        try:
            current = AcademyStatus(academy.status)
            target = AcademyStatus(str(target_value))
        except ValueError as error:
            raise ValidationError("Invalid academy status.") from error
        if target not in ACADEMY_STATUS_TRANSITIONS[current]:
            raise ConflictError(
                f"Academy status cannot transition from {current} to {target}.",
                "invalid_status_transition",
            )
        academy.status = target.value
        academy.archived_at = (
            datetime.now(timezone.utc)
            if target == AcademyStatus.ARCHIVED
            else None
        )

    def _audit(
        self,
        principal: Principal,
        academy: Academy,
        action: str,
        *,
        previous_data: dict | None = None,
        new_data: dict | None = None,
    ) -> None:
        self.audit.record(
            AuditEvent(
                academy_id=academy.id,
                actor_user_id=principal.user.id,
                entity_type="academy",
                entity_id=str(academy.id),
                action_type=action,
                previous_data=previous_data,
                new_data=new_data,
            )
        )
