from uuid import UUID

from sqlalchemy import func, select

from app.domain.scheduling_status import EnrollmentStatus
from app.extensions import db
from app.models.academic_class import AcademicClass
from app.models.class_student import ClassStudent
from app.repositories.base import BaseRepository


class ClassRepository(BaseRepository[AcademicClass]):
    def __init__(self) -> None:
        super().__init__(AcademicClass)

    def get_scoped(
        self,
        academy_id: UUID,
        branch_id: UUID,
        class_id: UUID,
    ) -> AcademicClass | None:
        return db.session.scalar(
            select(AcademicClass).where(
                AcademicClass.id == class_id,
                AcademicClass.academy_id == academy_id,
                AcademicClass.branch_id == branch_id,
            )
        )

    def get_by_code(
        self,
        academy_id: UUID,
        branch_id: UUID,
        class_code: str,
    ) -> AcademicClass | None:
        return db.session.scalar(
            select(AcademicClass).where(
                AcademicClass.academy_id == academy_id,
                AcademicClass.branch_id == branch_id,
                AcademicClass.class_code == class_code,
            )
        )

    def list_for_branch(
        self,
        academy_id: UUID,
        branch_id: UUID,
    ) -> list[AcademicClass]:
        return list(
            db.session.scalars(
                select(AcademicClass)
                .where(
                    AcademicClass.academy_id == academy_id,
                    AcademicClass.branch_id == branch_id,
                    AcademicClass.status != "archived",
                )
                .order_by(AcademicClass.class_name)
            )
        )

    def active_enrollment_count(self, class_id: UUID) -> int:
        return int(
            db.session.scalar(
                select(func.count())
                .select_from(ClassStudent)
                .where(
                    ClassStudent.class_id == class_id,
                    ClassStudent.enrollment_status == EnrollmentStatus.ACTIVE,
                )
            )
            or 0
        )


class ClassStudentRepository(BaseRepository[ClassStudent]):
    def __init__(self) -> None:
        super().__init__(ClassStudent)

    def get_enrollment(
        self,
        class_id: UUID,
        student_id: UUID,
    ) -> ClassStudent | None:
        return db.session.scalar(
            select(ClassStudent).where(
                ClassStudent.class_id == class_id,
                ClassStudent.student_id == student_id,
            )
        )

    def list_active_for_class(self, class_id: UUID) -> list[ClassStudent]:
        return list(
            db.session.scalars(
                select(ClassStudent).where(
                    ClassStudent.class_id == class_id,
                    ClassStudent.enrollment_status == EnrollmentStatus.ACTIVE,
                )
            )
        )
