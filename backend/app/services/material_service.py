from datetime import datetime, timezone
from uuid import UUID

from app.common.errors import ConflictError, NotFoundError, ValidationError
from app.domain.material_status import (
    MaterialDistributionStatus,
    MaterialStatus,
    MaterialVersionStatus,
)
from app.extensions import db
from app.models.material import Material
from app.models.material_distribution import MaterialDistribution
from app.models.material_version import MaterialVersion
from app.permissions.constants import Permission
from app.permissions.context import AuthorizationTarget, Principal
from app.repositories.class_repository import ClassRepository
from app.repositories.material_repository import (
    MaterialDistributionRepository,
    MaterialRepository,
    MaterialVersionRepository,
)
from app.repositories.notification_repository import NotificationRepository
from app.services.audit_log_service import AuditEvent, AuditLogService
from app.services.authorization_service import AuthorizationService
from app.services.notification_service import NotificationService


class MaterialService:
    def __init__(
        self,
        materials: MaterialRepository | None = None,
        versions: MaterialVersionRepository | None = None,
        distributions: MaterialDistributionRepository | None = None,
        classes: ClassRepository | None = None,
        notification_repository: NotificationRepository | None = None,
        notifications: NotificationService | None = None,
        audit: AuditLogService | None = None,
    ) -> None:
        self.materials = materials or MaterialRepository()
        self.versions = versions or MaterialVersionRepository()
        self.distributions = distributions or MaterialDistributionRepository()
        self.classes = classes or ClassRepository()
        self.notification_repository = (
            notification_repository or NotificationRepository()
        )
        self.notifications = notifications or NotificationService(
            self.notification_repository
        )
        self.audit = audit or AuditLogService()

    def list_repository(
        self,
        principal: Principal,
        academy_id: UUID,
    ) -> list[Material]:
        self._require_repository_view(principal, academy_id)
        return self.materials.list_for_academy(academy_id)

    def create(
        self,
        principal: Principal,
        *,
        academy_id: UUID,
        branch_id: UUID,
        class_id: UUID,
        material_code: str,
        title: str,
        material_type: str,
        description: str | None,
        file_data: dict[str, object],
    ) -> Material:
        target = self._target(academy_id, branch_id, class_id)
        AuthorizationService.require(principal, Permission.MATERIAL_UPLOAD, target)
        self._class(academy_id, branch_id, class_id)
        if self.materials.get_by_code(academy_id, material_code):
            raise ConflictError(
                "Material code already exists in this academy.",
                "material_code_exists",
            )
        material = Material(
            academy_id=academy_id,
            material_code=material_code,
            title=title,
            material_type=material_type,
            description=description,
            created_by=principal.user.id,
        )
        self.materials.add(material)
        db.session.flush()
        version = self._new_version(principal, material, file_data)
        self._audit(
            principal,
            material,
            "material.created",
            new_data=self.serialize(material),
        )
        self._audit_version(
            principal,
            version,
            "material.version_uploaded",
            new_data=self.serialize_version(version),
        )
        db.session.commit()
        return material

    def add_version(
        self,
        principal: Principal,
        *,
        academy_id: UUID,
        branch_id: UUID,
        class_id: UUID,
        material_id: UUID,
        file_data: dict[str, object],
    ) -> MaterialVersion:
        AuthorizationService.require(
            principal,
            Permission.MATERIAL_UPLOAD,
            self._target(academy_id, branch_id, class_id),
        )
        material = self._material(academy_id, material_id)
        if material.status == MaterialStatus.ARCHIVED:
            raise ConflictError(
                "Archived materials cannot receive new versions.",
                "material_archived",
            )
        version = self._new_version(principal, material, file_data)
        self._audit_version(
            principal,
            version,
            "material.version_uploaded",
            new_data=self.serialize_version(version),
        )
        db.session.commit()
        return version

    def approve_version(
        self,
        principal: Principal,
        *,
        academy_id: UUID,
        material_id: UUID,
        version_id: UUID,
    ) -> MaterialVersion:
        AuthorizationService.require(
            principal,
            Permission.MATERIAL_APPROVE,
            AuthorizationTarget(academy_id=academy_id),
        )
        version = self._version(academy_id, material_id, version_id)
        if version.status != MaterialVersionStatus.REVIEW:
            raise ConflictError(
                "This material version cannot be approved.",
                "material_version_not_approvable",
            )
        previous = self.serialize_version(version)
        version.status = MaterialVersionStatus.READY
        version.approved_by = principal.user.id
        version.approved_at = datetime.now(timezone.utc)
        self._audit_version(
            principal,
            version,
            "material.version_approved",
            previous_data=previous,
            new_data=self.serialize_version(version),
        )
        db.session.commit()
        return version

    def submit_version(
        self,
        principal: Principal,
        *,
        academy_id: UUID,
        branch_id: UUID,
        class_id: UUID,
        material_id: UUID,
        version_id: UUID,
    ) -> MaterialVersion:
        AuthorizationService.require(
            principal,
            Permission.MATERIAL_UPLOAD,
            self._target(academy_id, branch_id, class_id),
        )
        version = self._version(academy_id, material_id, version_id)
        if version.status != MaterialVersionStatus.DRAFT:
            raise ConflictError(
                "Only draft material versions can enter review.",
                "material_version_not_draft",
            )
        previous = self.serialize_version(version)
        version.status = MaterialVersionStatus.REVIEW
        self._audit_version(
            principal,
            version,
            "material.version_submitted",
            previous_data=previous,
            new_data=self.serialize_version(version),
        )
        db.session.commit()
        return version

    def distribute(
        self,
        principal: Principal,
        *,
        academy_id: UUID,
        branch_id: UUID,
        class_id: UUID,
        material_id: UUID,
        version_id: UUID,
    ) -> MaterialDistribution:
        AuthorizationService.require(
            principal,
            Permission.MATERIAL_DISTRIBUTE,
            self._target(academy_id, branch_id, class_id),
        )
        self._class(academy_id, branch_id, class_id)
        material = self._material(academy_id, material_id)
        version = self._version(academy_id, material_id, version_id)
        if (
            material.status != MaterialStatus.ACTIVE
            or version.status != MaterialVersionStatus.READY
        ):
            raise ConflictError(
                "Only ready versions of active materials can be distributed.",
                "material_version_not_ready",
            )
        distribution = self.distributions.get_target(
            material_id,
            branch_id,
            class_id,
        )
        previous = self.serialize_distribution(distribution) if distribution else None
        if distribution is None:
            distribution = MaterialDistribution(
                academy_id=academy_id,
                material_id=material_id,
                version_id=version_id,
                branch_id=branch_id,
                class_id=class_id,
                status=MaterialDistributionStatus.READY,
                distributed_by=principal.user.id,
            )
            self.distributions.add(distribution)
        elif distribution.version_id == version_id:
            return distribution
        else:
            distribution.version_id = version_id
            distribution.status = MaterialDistributionStatus.UPDATED
            distribution.distributed_by = principal.user.id
            distribution.distributed_at = datetime.now(timezone.utc)
        db.session.flush()
        self._audit_distribution(
            principal,
            distribution,
            "material.distributed",
            previous_data=previous,
            new_data=self.serialize_distribution(distribution),
        )
        self._notify_teachers(material, version, distribution)
        db.session.commit()
        return distribution

    def list_for_class(
        self,
        principal: Principal,
        *,
        academy_id: UUID,
        branch_id: UUID,
        class_id: UUID,
    ) -> list[MaterialDistribution]:
        AuthorizationService.require(
            principal,
            Permission.MATERIAL_VIEW,
            self._target(academy_id, branch_id, class_id),
        )
        self._class(academy_id, branch_id, class_id)
        return self.distributions.list_for_class(
            academy_id,
            branch_id,
            class_id,
        )

    def archive(
        self,
        principal: Principal,
        *,
        academy_id: UUID,
        material_id: UUID,
    ) -> Material:
        AuthorizationService.require(
            principal,
            Permission.MATERIAL_ARCHIVE,
            AuthorizationTarget(academy_id=academy_id),
        )
        material = self._material(academy_id, material_id)
        if material.status == MaterialStatus.ARCHIVED:
            return material
        previous = self.serialize(material)
        material.status = MaterialStatus.ARCHIVED
        material.archived_by = principal.user.id
        material.archived_at = datetime.now(timezone.utc)
        for distribution in material.distributions:
            distribution.status = MaterialDistributionStatus.ARCHIVED
        self._audit(
            principal,
            material,
            "material.archived",
            previous_data=previous,
            new_data=self.serialize(material),
        )
        db.session.commit()
        return material

    @staticmethod
    def serialize(material: Material) -> dict[str, object]:
        latest = material.versions[-1] if material.versions else None
        return {
            "id": str(material.id),
            "academy_id": str(material.academy_id),
            "material_code": material.material_code,
            "title": material.title,
            "material_type": material.material_type,
            "description": material.description,
            "status": material.status,
            "latest_version": (
                MaterialService.serialize_version(latest) if latest else None
            ),
            "version_count": len(material.versions),
        }

    @staticmethod
    def serialize_version(version: MaterialVersion) -> dict[str, object]:
        base = (
            f"/api/v1/academies/{version.academy_id}/materials/"
            f"{version.material_id}/versions/{version.id}"
        )
        return {
            "id": str(version.id),
            "version_number": version.version_number,
            "version_label": version.version_label,
            "file_name": version.file_name,
            "mime_type": version.mime_type,
            "file_size": version.file_size,
            "checksum_sha256": version.checksum_sha256,
            "status": version.status,
            "preview_url": f"{base}/access-metadata?disposition=inline",
            "download_url": f"{base}/access-metadata?disposition=attachment",
        }

    @staticmethod
    def serialize_distribution(
        distribution: MaterialDistribution,
    ) -> dict[str, object]:
        version = MaterialService.serialize_version(distribution.version)
        query = (
            f"branch_id={distribution.branch_id}&class_id={distribution.class_id}"
        )
        base = (
            f"/api/v1/academies/{distribution.academy_id}/materials/"
            f"{distribution.material_id}/versions/{distribution.version_id}"
        )
        version["preview_url"] = (
            f"{base}/access-metadata?disposition=inline&{query}"
        )
        version["download_url"] = (
            f"{base}/access-metadata?disposition=attachment&{query}"
        )
        return {
            "id": str(distribution.id),
            "material_id": str(distribution.material_id),
            "version_id": str(distribution.version_id),
            "branch_id": str(distribution.branch_id),
            "class_id": str(distribution.class_id),
            "status": distribution.status,
            "material": MaterialService.serialize(distribution.material),
            "version": version,
        }

    def access_metadata(
        self,
        principal: Principal,
        *,
        academy_id: UUID,
        material_id: UUID,
        version_id: UUID,
        branch_id: UUID,
        class_id: UUID,
        disposition: str,
    ) -> dict[str, object]:
        AuthorizationService.require(
            principal,
            Permission.MATERIAL_VIEW,
            self._target(academy_id, branch_id, class_id),
        )
        version = self._version(academy_id, material_id, version_id)
        distribution = self.distributions.get_target(
            material_id,
            branch_id,
            class_id,
        )
        if distribution is None or distribution.version_id != version_id:
            raise NotFoundError("Material distribution")
        if version.status != MaterialVersionStatus.READY:
            raise ConflictError(
                "Only ready material versions can be accessed.",
                "material_version_not_ready",
            )
        if disposition not in {"inline", "attachment"}:
            raise ValidationError("Invalid material disposition.")
        return {
            "storage_key": version.storage_key,
            "file_name": version.file_name,
            "mime_type": version.mime_type,
            "file_size": version.file_size,
            "checksum_sha256": version.checksum_sha256,
            "content_disposition": disposition,
            "delivery": "storage_provider_pending",
        }

    def _new_version(
        self,
        principal: Principal,
        material: Material,
        file_data: dict[str, object],
    ) -> MaterialVersion:
        number = self.versions.next_version_number(material.id)
        version = MaterialVersion(
            academy_id=material.academy_id,
            material_id=material.id,
            version_number=number,
            version_label=f"v{number}",
            uploaded_by=principal.user.id,
            **file_data,
        )
        self.versions.add(version)
        db.session.flush()
        return version

    def _notify_teachers(
        self,
        material: Material,
        version: MaterialVersion,
        distribution: MaterialDistribution,
    ) -> None:
        recipients = self.notification_repository.teacher_user_ids_for_class(
            distribution.academy_id,
            distribution.branch_id,
            distribution.class_id,
        )
        for recipient in recipients:
            self.notifications.emit(
                academy_id=distribution.academy_id,
                recipient_user_id=recipient,
                notification_type="material.updated",
                priority="medium",
                title="Class material updated",
                payload={
                    "material_id": str(material.id),
                    "version_id": str(version.id),
                    "class_id": str(distribution.class_id),
                    "branch_id": str(distribution.branch_id),
                    "version_label": version.version_label,
                },
                dedup_key=(
                    f"material:{material.id}:version:{version.id}:"
                    f"class:{distribution.class_id}"
                ),
            )

    def _class(self, academy_id: UUID, branch_id: UUID, class_id: UUID):
        academic_class = self.classes.get_scoped(academy_id, branch_id, class_id)
        if academic_class is None:
            raise NotFoundError("Class")
        return academic_class

    @staticmethod
    def _require_repository_view(
        principal: Principal,
        academy_id: UUID,
    ) -> None:
        for assignment in principal.assignments:
            target = AuthorizationTarget(
                academy_id=academy_id,
                branch_id=assignment.branch_id,
                class_id=assignment.scope_id,
            )
            if AuthorizationService._assignment_allows(
                assignment,
                Permission.MATERIAL_VIEW,
                target,
                principal.user.id,
            ):
                return
        AuthorizationService.require(
            principal,
            Permission.MATERIAL_VIEW,
            AuthorizationTarget(academy_id=academy_id),
        )

    def _material(self, academy_id: UUID, material_id: UUID) -> Material:
        material = self.materials.get_scoped(academy_id, material_id)
        if material is None:
            raise NotFoundError("Material")
        return material

    def _version(
        self,
        academy_id: UUID,
        material_id: UUID,
        version_id: UUID,
    ) -> MaterialVersion:
        version = self.versions.get_scoped(academy_id, material_id, version_id)
        if version is None:
            raise NotFoundError("Material version")
        return version

    @staticmethod
    def _target(
        academy_id: UUID,
        branch_id: UUID,
        class_id: UUID,
    ) -> AuthorizationTarget:
        return AuthorizationTarget(
            academy_id=academy_id,
            branch_id=branch_id,
            class_id=class_id,
        )

    def _audit(
        self,
        principal: Principal,
        material: Material,
        action: str,
        **data,
    ) -> None:
        self.audit.record(
            AuditEvent(
                academy_id=material.academy_id,
                actor_user_id=principal.user.id,
                entity_type="material",
                entity_id=str(material.id),
                action_type=action,
                **data,
            )
        )

    def _audit_version(
        self,
        principal: Principal,
        version: MaterialVersion,
        action: str,
        **data,
    ) -> None:
        self.audit.record(
            AuditEvent(
                academy_id=version.academy_id,
                actor_user_id=principal.user.id,
                entity_type="material_version",
                entity_id=str(version.id),
                action_type=action,
                **data,
            )
        )

    def _audit_distribution(
        self,
        principal: Principal,
        distribution: MaterialDistribution,
        action: str,
        **data,
    ) -> None:
        self.audit.record(
            AuditEvent(
                academy_id=distribution.academy_id,
                branch_id=distribution.branch_id,
                actor_user_id=principal.user.id,
                entity_type="material_distribution",
                entity_id=str(distribution.id),
                action_type=action,
                **data,
            )
        )
