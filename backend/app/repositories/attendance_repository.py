from uuid import UUID

from sqlalchemy import select

from app.extensions import db
from app.models.attendance import Attendance
from app.models.attendance_edit_request import AttendanceEditRequest
from app.repositories.base import BaseRepository


class AttendanceRepository(BaseRepository[Attendance]):
    def __init__(self) -> None:
        super().__init__(Attendance)

    def get_scoped(
        self,
        academy_id: UUID,
        branch_id: UUID,
        attendance_id: UUID,
    ) -> Attendance | None:
        return db.session.scalar(
            select(Attendance).where(
                Attendance.id == attendance_id,
                Attendance.academy_id == academy_id,
                Attendance.branch_id == branch_id,
            )
        )

    def get_for_session_student(
        self,
        session_id: UUID,
        student_id: UUID,
    ) -> Attendance | None:
        return db.session.scalar(
            select(Attendance).where(
                Attendance.session_id == session_id,
                Attendance.student_id == student_id,
            )
        )

    def list_for_session(
        self,
        academy_id: UUID,
        branch_id: UUID,
        session_id: UUID,
    ) -> list[Attendance]:
        return list(
            db.session.scalars(
                select(Attendance)
                .where(
                    Attendance.academy_id == academy_id,
                    Attendance.branch_id == branch_id,
                    Attendance.session_id == session_id,
                )
                .order_by(Attendance.student_id)
            )
        )


class AttendanceEditRequestRepository(BaseRepository[AttendanceEditRequest]):
    def __init__(self) -> None:
        super().__init__(AttendanceEditRequest)

    def get_scoped_for_update(
        self,
        academy_id: UUID,
        branch_id: UUID,
        request_id: UUID,
    ) -> AttendanceEditRequest | None:
        return db.session.scalar(
            select(AttendanceEditRequest)
            .where(
                AttendanceEditRequest.id == request_id,
                AttendanceEditRequest.academy_id == academy_id,
                AttendanceEditRequest.branch_id == branch_id,
            )
            .with_for_update()
        )

    def pending_for_attendance(
        self,
        attendance_id: UUID,
    ) -> AttendanceEditRequest | None:
        return db.session.scalar(
            select(AttendanceEditRequest).where(
                AttendanceEditRequest.attendance_id == attendance_id,
                AttendanceEditRequest.status == "pending",
            )
        )
