from uuid import UUID

from app.common.errors import ConflictError, ValidationError
from app.domain.scheduling_status import RoomStatus
from app.extensions import db
from app.models.room import Room
from app.permissions.constants import Permission
from app.permissions.context import AuthorizationTarget, Principal
from app.repositories.branch_repository import BranchRepository
from app.repositories.room_repository import RoomRepository
from app.services.audit_log_service import AuditEvent, AuditLogService
from app.services.authorization_service import AuthorizationService


class RoomService:
    def __init__(
        self,
        repository: RoomRepository | None = None,
        branches: BranchRepository | None = None,
        audit: AuditLogService | None = None,
    ) -> None:
        self.repository = repository or RoomRepository()
        self.branches = branches or BranchRepository()
        self.audit = audit or AuditLogService()

    def list_for_branch(
        self,
        principal: Principal,
        academy_id: UUID,
        branch_id: UUID,
    ) -> list[Room]:
        AuthorizationService.require(
            principal,
            Permission.CLASS_VIEW,
            AuthorizationTarget(academy_id=academy_id, branch_id=branch_id),
        )
        return self.repository.list_for_branch(academy_id, branch_id)

    def create(
        self,
        principal: Principal,
        *,
        academy_id: UUID,
        branch_id: UUID,
        room_code: str,
        room_name: str,
        capacity: int,
        room_type: str | None = None,
    ) -> Room:
        AuthorizationService.require(
            principal,
            Permission.CLASS_MANAGE,
            AuthorizationTarget(academy_id=academy_id, branch_id=branch_id),
        )
        branch = self.branches.get_by_id(branch_id)
        if branch is None or branch.academy_id != academy_id or branch.status != "active":
            raise ValidationError("Room branch must be active and belong to the academy.")
        code = self._required_text(room_code, "Room code").upper()
        if self.repository.get_by_code(academy_id, branch_id, code):
            raise ConflictError(
                "A room with this code already exists in the branch.",
                "room_code_exists",
            )
        room = Room(
            academy_id=academy_id,
            branch_id=branch_id,
            room_code=code,
            room_name=self._required_text(room_name, "Room name"),
            capacity=capacity,
            room_type=room_type.strip() if room_type else None,
            status=RoomStatus.AVAILABLE,
            created_by=principal.user.id,
            updated_by=principal.user.id,
        )
        self.repository.add(room)
        db.session.flush()
        self.audit.record(
            AuditEvent(
                academy_id=academy_id,
                branch_id=branch_id,
                actor_user_id=principal.user.id,
                entity_type="room",
                entity_id=str(room.id),
                action_type="room.created",
                new_data=self.serialize(room),
            )
        )
        db.session.commit()
        return room

    @staticmethod
    def serialize(room: Room) -> dict[str, object]:
        return {
            "id": str(room.id),
            "academy_id": str(room.academy_id),
            "branch_id": str(room.branch_id),
            "room_code": room.room_code,
            "room_name": room.room_name,
            "capacity": room.capacity,
            "room_type": room.room_type,
            "status": room.status,
        }

    @staticmethod
    def _required_text(value: object, label: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValidationError(f"{label} is required.")
        return value.strip()
