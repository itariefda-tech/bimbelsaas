from datetime import datetime
from uuid import UUID

from sqlalchemy import distinct, select

from app.domain.scheduling_status import BLOCKING_SCHEDULE_STATUSES, EnrollmentStatus
from app.extensions import db
from app.models.class_session import ClassSession
from app.models.class_student import ClassStudent
from app.models.schedule import Schedule
from app.models.schedule_change_request import ScheduleChangeRequest
from app.repositories.base import BaseRepository


class ScheduleRepository(BaseRepository[Schedule]):
    def __init__(self) -> None:
        super().__init__(Schedule)

    def get_scoped(
        self,
        academy_id: UUID,
        branch_id: UUID,
        schedule_id: UUID,
    ) -> Schedule | None:
        return db.session.scalar(
            select(Schedule).where(
                Schedule.id == schedule_id,
                Schedule.academy_id == academy_id,
                Schedule.branch_id == branch_id,
            )
        )

    def list_for_branch(
        self,
        academy_id: UUID,
        branch_id: UUID,
    ) -> list[Schedule]:
        return list(
            db.session.scalars(
                select(Schedule)
                .where(
                    Schedule.academy_id == academy_id,
                    Schedule.branch_id == branch_id,
                )
                .order_by(Schedule.starts_at, Schedule.id)
            )
        )

    def list_for_teacher_window(
        self,
        academy_id: UUID,
        teacher_id: UUID,
        starts_at: datetime,
        ends_at: datetime,
    ) -> list[Schedule]:
        return list(
            db.session.scalars(
                select(Schedule)
                .where(
                    Schedule.academy_id == academy_id,
                    Schedule.teacher_id == teacher_id,
                    Schedule.starts_at < ends_at,
                    Schedule.ends_at > starts_at,
                )
                .order_by(Schedule.starts_at, Schedule.id)
            )
        )

    def overlapping_for_teacher(
        self,
        academy_id: UUID,
        teacher_id: UUID,
        starts_at: datetime,
        ends_at: datetime,
        exclude_schedule_id: UUID | None = None,
    ) -> list[Schedule]:
        return self._overlapping(
            Schedule.academy_id == academy_id,
            Schedule.teacher_id == teacher_id,
            starts_at=starts_at,
            ends_at=ends_at,
            exclude_schedule_id=exclude_schedule_id,
        )

    def overlapping_for_room(
        self,
        academy_id: UUID,
        room_id: UUID,
        starts_at: datetime,
        ends_at: datetime,
        exclude_schedule_id: UUID | None = None,
    ) -> list[Schedule]:
        return self._overlapping(
            Schedule.academy_id == academy_id,
            Schedule.room_id == room_id,
            starts_at=starts_at,
            ends_at=ends_at,
            exclude_schedule_id=exclude_schedule_id,
        )

    def overlapping_for_class(
        self,
        academy_id: UUID,
        class_id: UUID,
        starts_at: datetime,
        ends_at: datetime,
        exclude_schedule_id: UUID | None = None,
    ) -> list[Schedule]:
        return self._overlapping(
            Schedule.academy_id == academy_id,
            Schedule.class_id == class_id,
            starts_at=starts_at,
            ends_at=ends_at,
            exclude_schedule_id=exclude_schedule_id,
        )

    def overlapping_for_students(
        self,
        academy_id: UUID,
        student_ids: set[UUID],
        starts_at: datetime,
        ends_at: datetime,
        exclude_schedule_id: UUID | None = None,
    ) -> list[Schedule]:
        if not student_ids:
            return []
        query = (
            select(Schedule)
            .join(ClassStudent, ClassStudent.class_id == Schedule.class_id)
            .where(
                Schedule.academy_id == academy_id,
                ClassStudent.academy_id == academy_id,
                ClassStudent.student_id.in_(student_ids),
                ClassStudent.enrollment_status == EnrollmentStatus.ACTIVE,
                Schedule.status.in_(BLOCKING_SCHEDULE_STATUSES),
                Schedule.starts_at < ends_at,
                Schedule.ends_at > starts_at,
            )
            .distinct()
        )
        if exclude_schedule_id is not None:
            query = query.where(Schedule.id != exclude_schedule_id)
        return list(db.session.scalars(query))

    def student_ids_with_overlaps(
        self,
        academy_id: UUID,
        student_ids: set[UUID],
        starts_at: datetime,
        ends_at: datetime,
        exclude_schedule_id: UUID | None = None,
    ) -> set[UUID]:
        if not student_ids:
            return set()
        query = (
            select(distinct(ClassStudent.student_id))
            .join(Schedule, Schedule.class_id == ClassStudent.class_id)
            .where(
                Schedule.academy_id == academy_id,
                ClassStudent.academy_id == academy_id,
                ClassStudent.student_id.in_(student_ids),
                ClassStudent.enrollment_status == EnrollmentStatus.ACTIVE,
                Schedule.status.in_(BLOCKING_SCHEDULE_STATUSES),
                Schedule.starts_at < ends_at,
                Schedule.ends_at > starts_at,
            )
        )
        if exclude_schedule_id is not None:
            query = query.where(Schedule.id != exclude_schedule_id)
        return set(db.session.scalars(query))

    def _overlapping(
        self,
        *criteria,
        starts_at: datetime,
        ends_at: datetime,
        exclude_schedule_id: UUID | None,
    ) -> list[Schedule]:
        query = select(Schedule).where(
            *criteria,
            Schedule.status.in_(BLOCKING_SCHEDULE_STATUSES),
            Schedule.starts_at < ends_at,
            Schedule.ends_at > starts_at,
        )
        if exclude_schedule_id is not None:
            query = query.where(Schedule.id != exclude_schedule_id)
        return list(db.session.scalars(query))


class ClassSessionRepository(BaseRepository[ClassSession]):
    def __init__(self) -> None:
        super().__init__(ClassSession)

    def get_scoped(
        self,
        academy_id: UUID,
        branch_id: UUID,
        session_id: UUID,
    ) -> ClassSession | None:
        return db.session.scalar(
            select(ClassSession).where(
                ClassSession.id == session_id,
                ClassSession.academy_id == academy_id,
                ClassSession.branch_id == branch_id,
            )
        )

    def get_scoped_for_update(
        self,
        academy_id: UUID,
        branch_id: UUID,
        session_id: UUID,
    ) -> ClassSession | None:
        return db.session.scalar(
            select(ClassSession)
            .where(
                ClassSession.id == session_id,
                ClassSession.academy_id == academy_id,
                ClassSession.branch_id == branch_id,
            )
            .with_for_update()
        )


class ScheduleChangeRequestRepository(BaseRepository[ScheduleChangeRequest]):
    def __init__(self) -> None:
        super().__init__(ScheduleChangeRequest)

    def get_scoped(
        self,
        academy_id: UUID,
        branch_id: UUID,
        request_id: UUID,
    ) -> ScheduleChangeRequest | None:
        return db.session.scalar(
            select(ScheduleChangeRequest).where(
                ScheduleChangeRequest.id == request_id,
                ScheduleChangeRequest.academy_id == academy_id,
                ScheduleChangeRequest.branch_id == branch_id,
            )
        )

    def get_scoped_for_update(
        self,
        academy_id: UUID,
        branch_id: UUID,
        request_id: UUID,
    ) -> ScheduleChangeRequest | None:
        return db.session.scalar(
            select(ScheduleChangeRequest)
            .where(
                ScheduleChangeRequest.id == request_id,
                ScheduleChangeRequest.academy_id == academy_id,
                ScheduleChangeRequest.branch_id == branch_id,
            )
            .with_for_update()
        )

    def list_for_schedule(
        self,
        academy_id: UUID,
        branch_id: UUID,
        schedule_id: UUID,
    ) -> list[ScheduleChangeRequest]:
        return list(
            db.session.scalars(
                select(ScheduleChangeRequest)
                .where(
                    ScheduleChangeRequest.academy_id == academy_id,
                    ScheduleChangeRequest.branch_id == branch_id,
                    ScheduleChangeRequest.schedule_id == schedule_id,
                )
                .order_by(
                    ScheduleChangeRequest.requested_at,
                    ScheduleChangeRequest.id,
                )
            )
        )

    def pending_for_schedule(
        self,
        academy_id: UUID,
        branch_id: UUID,
        schedule_id: UUID,
    ) -> ScheduleChangeRequest | None:
        return db.session.scalar(
            select(ScheduleChangeRequest).where(
                ScheduleChangeRequest.academy_id == academy_id,
                ScheduleChangeRequest.branch_id == branch_id,
                ScheduleChangeRequest.schedule_id == schedule_id,
                ScheduleChangeRequest.status == "pending",
            )
        )
