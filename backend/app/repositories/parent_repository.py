from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import joinedload

from app.domain.attendance_status import AttendanceSheetStatus
from app.domain.lesson_summary_status import LessonSummaryStatus
from app.domain.scheduling_status import EnrollmentStatus
from app.extensions import db
from app.models.academic_class import AcademicClass
from app.models.attendance import Attendance
from app.models.branch import Branch
from app.models.class_session import ClassSession
from app.models.class_student import ClassStudent
from app.models.lesson_summary import LessonSummary
from app.models.parent import Parent
from app.models.parent_student import ParentStudent
from app.models.schedule import Schedule
from app.models.student import Student
from app.models.teacher import Teacher
from app.repositories.base import BaseRepository


class ParentRepository(BaseRepository[Parent]):
    def __init__(self) -> None:
        super().__init__(Parent)

    def get_by_user(self, academy_id: UUID, user_id: UUID) -> Parent | None:
        return db.session.scalar(
            select(Parent).where(
                Parent.academy_id == academy_id,
                Parent.user_id == user_id,
            )
        )


class ParentStudentRepository(BaseRepository[ParentStudent]):
    def __init__(self) -> None:
        super().__init__(ParentStudent)

    def get_link(
        self,
        academy_id: UUID,
        parent_id: UUID,
        student_id: UUID,
    ) -> ParentStudent | None:
        return db.session.scalar(
            select(ParentStudent).where(
                ParentStudent.academy_id == academy_id,
                ParentStudent.parent_id == parent_id,
                ParentStudent.student_id == student_id,
            )
        )

    def list_active_for_parent(
        self,
        academy_id: UUID,
        parent_id: UUID,
    ) -> list[ParentStudent]:
        return list(
            db.session.scalars(
                select(ParentStudent)
                .options(joinedload(ParentStudent.student))
                .join(Student, Student.id == ParentStudent.student_id)
                .where(
                    ParentStudent.academy_id == academy_id,
                    ParentStudent.parent_id == parent_id,
                    ParentStudent.relationship_status == "active",
                    Student.status != "archived",
                )
                .order_by(Student.full_name, ParentStudent.id)
            )
        )

    def active_link(
        self,
        academy_id: UUID,
        parent_id: UUID,
        student_id: UUID,
    ) -> ParentStudent | None:
        return db.session.scalar(
            select(ParentStudent)
            .options(joinedload(ParentStudent.student))
            .where(
                ParentStudent.academy_id == academy_id,
                ParentStudent.parent_id == parent_id,
                ParentStudent.student_id == student_id,
                ParentStudent.relationship_status == "active",
            )
        )

    def active_classes(
        self,
        academy_id: UUID,
        student_id: UUID,
    ) -> list[AcademicClass]:
        return list(
            db.session.scalars(
                select(AcademicClass)
                .join(ClassStudent, ClassStudent.class_id == AcademicClass.id)
                .where(
                    AcademicClass.academy_id == academy_id,
                    ClassStudent.academy_id == academy_id,
                    ClassStudent.student_id == student_id,
                    ClassStudent.enrollment_status == EnrollmentStatus.ACTIVE,
                    AcademicClass.status != "archived",
                )
                .order_by(AcademicClass.class_name)
            )
        )

    def attendance_counts(
        self,
        academy_id: UUID,
        student_id: UUID,
    ) -> dict[str, int]:
        rows = db.session.execute(
            select(Attendance.attendance_status, func.count())
            .join(ClassSession, ClassSession.id == Attendance.session_id)
            .where(
                Attendance.academy_id == academy_id,
                Attendance.student_id == student_id,
                ClassSession.attendance_status
                == AttendanceSheetStatus.FINALIZED,
            )
            .group_by(Attendance.attendance_status)
        )
        return {status: int(count) for status, count in rows}

    def progress_snapshot(
        self,
        academy_id: UUID,
        student_id: UUID,
    ) -> dict[str, int]:
        attendance = self.attendance_counts(academy_id, student_id)
        published_summaries = int(
            db.session.scalar(
                select(func.count(LessonSummary.id))
                .join(
                    Attendance,
                    (Attendance.session_id == LessonSummary.session_id)
                    & (Attendance.student_id == student_id),
                )
                .join(ClassSession, ClassSession.id == Attendance.session_id)
                .where(
                    LessonSummary.academy_id == academy_id,
                    LessonSummary.status == LessonSummaryStatus.PUBLISHED,
                    ClassSession.attendance_status
                    == AttendanceSheetStatus.FINALIZED,
                )
            )
            or 0
        )
        homework_count = int(
            db.session.scalar(
                select(func.count(LessonSummary.id))
                .join(
                    Attendance,
                    (Attendance.session_id == LessonSummary.session_id)
                    & (Attendance.student_id == student_id),
                )
                .join(ClassSession, ClassSession.id == Attendance.session_id)
                .where(
                    LessonSummary.academy_id == academy_id,
                    LessonSummary.status == LessonSummaryStatus.PUBLISHED,
                    LessonSummary.homework.is_not(None),
                    LessonSummary.homework != "",
                    ClassSession.attendance_status
                    == AttendanceSheetStatus.FINALIZED,
                )
            )
            or 0
        )
        return {
            **attendance,
            "published_summaries": published_summaries,
            "homework_assigned": homework_count,
        }

    def attendance_history(
        self,
        academy_id: UUID,
        student_id: UUID,
        limit: int,
    ) -> list[tuple[Attendance, Schedule, AcademicClass, Branch]]:
        return list(
            db.session.execute(
                select(Attendance, Schedule, AcademicClass, Branch)
                .join(ClassSession, ClassSession.id == Attendance.session_id)
                .join(Schedule, Schedule.id == Attendance.schedule_id)
                .join(AcademicClass, AcademicClass.id == Attendance.class_id)
                .join(Branch, Branch.id == Attendance.branch_id)
                .where(
                    Attendance.academy_id == academy_id,
                    Attendance.student_id == student_id,
                    ClassSession.attendance_status
                    == AttendanceSheetStatus.FINALIZED,
                )
                .order_by(Schedule.starts_at.desc(), Attendance.id.desc())
                .limit(limit)
            ).all()
        )

    def published_summaries(
        self,
        academy_id: UUID,
        student_id: UUID,
        limit: int,
    ) -> list[tuple[LessonSummary, Schedule, AcademicClass, Branch]]:
        return list(
            db.session.execute(
                select(LessonSummary, Schedule, AcademicClass, Branch)
                .join(
                    Attendance,
                    (Attendance.session_id == LessonSummary.session_id)
                    & (Attendance.student_id == student_id),
                )
                .join(Schedule, Schedule.id == LessonSummary.schedule_id)
                .join(AcademicClass, AcademicClass.id == LessonSummary.class_id)
                .join(Branch, Branch.id == LessonSummary.branch_id)
                .where(
                    LessonSummary.academy_id == academy_id,
                    LessonSummary.status == LessonSummaryStatus.PUBLISHED,
                )
                .order_by(
                    LessonSummary.published_at.desc(),
                    LessonSummary.id.desc(),
                )
                .limit(limit)
            ).all()
        )

    def schedule_window(
        self,
        academy_id: UUID,
        student_id: UUID,
        starts_at: datetime,
        ends_at: datetime,
    ) -> list[Schedule]:
        return list(
            db.session.scalars(
                select(Schedule)
                .options(
                    joinedload(Schedule.academic_class),
                    joinedload(Schedule.teacher),
                    joinedload(Schedule.room),
                    joinedload(Schedule.session),
                )
                .join(ClassStudent, ClassStudent.class_id == Schedule.class_id)
                .where(
                    Schedule.academy_id == academy_id,
                    ClassStudent.academy_id == academy_id,
                    ClassStudent.student_id == student_id,
                    ClassStudent.enrollment_status == EnrollmentStatus.ACTIVE,
                    Schedule.starts_at < ends_at,
                    Schedule.ends_at > starts_at,
                )
                .order_by(Schedule.starts_at, Schedule.id)
            ).unique()
        )

    def active_teachers(
        self,
        academy_id: UUID,
        class_ids: set[UUID],
    ) -> list[Teacher]:
        if not class_ids:
            return []
        return list(
            db.session.scalars(
                select(Teacher)
                .join(Schedule, Schedule.teacher_id == Teacher.id)
                .where(
                    Teacher.academy_id == academy_id,
                    Teacher.status == "active",
                    Schedule.class_id.in_(class_ids),
                )
                .distinct()
                .order_by(Teacher.full_name)
            )
        )
