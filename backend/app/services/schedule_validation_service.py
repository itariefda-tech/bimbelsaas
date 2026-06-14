from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from app.common.errors import SchedulingConflictError, ValidationError
from app.domain.organization_status import AcademyStatus, BranchStatus
from app.domain.profile_status import ProfileStatus, TeacherBranchStatus
from app.domain.scheduling_status import ClassStatus, EnrollmentStatus, RoomStatus
from app.models.academic_class import AcademicClass
from app.models.room import Room
from app.models.student import Student
from app.models.teacher import Teacher
from app.repositories.academy_repository import AcademyRepository
from app.repositories.branch_repository import BranchRepository
from app.repositories.class_repository import ClassRepository, ClassStudentRepository
from app.repositories.room_repository import RoomRepository
from app.repositories.schedule_repository import ScheduleRepository
from app.repositories.student_repository import StudentRepository
from app.repositories.teacher_branch_repository import TeacherBranchRepository
from app.repositories.teacher_repository import TeacherRepository
from app.services.cross_branch_policy import CrossBranchPolicy


@dataclass(frozen=True)
class ScheduleCandidate:
    academy_id: UUID
    branch_id: UUID
    class_id: UUID
    teacher_id: UUID
    room_id: UUID
    starts_at: datetime
    ends_at: datetime
    exclude_schedule_id: UUID | None = None


@dataclass
class ScheduleValidationContext:
    candidate: ScheduleCandidate
    academic_class: AcademicClass | None = None
    teacher: Teacher | None = None
    room: Room | None = None
    students: list[Student] = field(default_factory=list)


class ScheduleValidationService:
    validation_order = (
        "branch",
        "teacher",
        "room",
        "student",
        "time",
        "cross_branch",
    )

    def __init__(
        self,
        academies: AcademyRepository | None = None,
        branches: BranchRepository | None = None,
        classes: ClassRepository | None = None,
        enrollments: ClassStudentRepository | None = None,
        teachers: TeacherRepository | None = None,
        teacher_branches: TeacherBranchRepository | None = None,
        rooms: RoomRepository | None = None,
        students: StudentRepository | None = None,
        schedules: ScheduleRepository | None = None,
        cross_branch: CrossBranchPolicy | None = None,
    ) -> None:
        self.academies = academies or AcademyRepository()
        self.branches = branches or BranchRepository()
        self.classes = classes or ClassRepository()
        self.enrollments = enrollments or ClassStudentRepository()
        self.teachers = teachers or TeacherRepository()
        self.teacher_branches = teacher_branches or TeacherBranchRepository()
        self.rooms = rooms or RoomRepository()
        self.students = students or StudentRepository()
        self.schedules = schedules or ScheduleRepository()
        self.cross_branch = cross_branch or CrossBranchPolicy()

    def validate(self, candidate: ScheduleCandidate) -> ScheduleValidationContext:
        if candidate.ends_at <= candidate.starts_at:
            raise ValidationError("Schedule end must be after schedule start.")
        context = ScheduleValidationContext(candidate=candidate)
        self._validate_branch(context)
        self._validate_teacher(context)
        self._validate_room(context)
        self._validate_students(context)
        self._validate_class_time(context)
        self._validate_cross_branch(context)
        return context

    def _validate_branch(self, context: ScheduleValidationContext) -> None:
        item = context.candidate
        academy = self.academies.get_by_id(item.academy_id)
        branch = self.branches.get_by_id(item.branch_id)
        academic_class = self.classes.get_scoped(
            item.academy_id,
            item.branch_id,
            item.class_id,
        )
        if academy is None or academy.status != AcademyStatus.ACTIVE:
            self._conflict("Academy is not operational.", "academy_not_active", "branch")
        if branch is None or branch.status != BranchStatus.ACTIVE:
            self._conflict("Branch is not operational.", "branch_not_active", "branch")
        if academic_class is None or academic_class.status != ClassStatus.ACTIVE:
            self._conflict("Class is not active in this branch.", "class_not_active", "branch")
        context.academic_class = academic_class

    def _validate_teacher(self, context: ScheduleValidationContext) -> None:
        item = context.candidate
        teacher = self.teachers.get_scoped(item.academy_id, item.teacher_id)
        assignment = self.teacher_branches.get_assignment(
            item.teacher_id,
            item.branch_id,
        )
        if teacher is None or teacher.status != ProfileStatus.ACTIVE:
            self._conflict("Teacher is not active.", "teacher_not_active", "teacher")
        if (
            assignment is None
            or assignment.assignment_status != TeacherBranchStatus.ACTIVE
        ):
            self._conflict(
                "Teacher is not assigned to this branch.",
                "teacher_branch_not_assigned",
                "teacher",
            )
        overlaps = self.schedules.overlapping_for_teacher(
            item.academy_id,
            item.teacher_id,
            item.starts_at,
            item.ends_at,
            item.exclude_schedule_id,
        )
        if overlaps:
            self._overlap(
                "Teacher already has an overlapping schedule.",
                "teacher_schedule_conflict",
                "teacher",
                overlaps,
            )
        context.teacher = teacher

    def _validate_room(self, context: ScheduleValidationContext) -> None:
        item = context.candidate
        room = self.rooms.get_scoped(item.academy_id, item.branch_id, item.room_id)
        if room is None or room.status != RoomStatus.AVAILABLE:
            self._conflict("Room is not available.", "room_not_available", "room")
        enrollment_count = self.classes.active_enrollment_count(item.class_id)
        if room.capacity < enrollment_count:
            self._conflict(
                "Room capacity is lower than active class enrollment.",
                "room_capacity_exceeded",
                "room",
            )
        overlaps = self.schedules.overlapping_for_room(
            item.academy_id,
            item.room_id,
            item.starts_at,
            item.ends_at,
            item.exclude_schedule_id,
        )
        if overlaps:
            self._overlap(
                "Room already has an overlapping schedule.",
                "room_schedule_conflict",
                "room",
                overlaps,
            )
        context.room = room

    def _validate_students(self, context: ScheduleValidationContext) -> None:
        item = context.candidate
        enrollments = self.enrollments.list_active_for_class(item.class_id)
        students: list[Student] = []
        for enrollment in enrollments:
            student = self.students.get_scoped(item.academy_id, enrollment.student_id)
            if student is None or student.status != ProfileStatus.ACTIVE:
                self._conflict(
                    "Class contains an inactive student.",
                    "student_not_active",
                    "student",
                )
            students.append(student)
        student_ids = {student.id for student in students}
        overlapping_students = self.schedules.student_ids_with_overlaps(
            item.academy_id,
            student_ids,
            item.starts_at,
            item.ends_at,
            item.exclude_schedule_id,
        )
        if overlapping_students:
            raise SchedulingConflictError(
                "One or more students have an overlapping schedule.",
                code="student_schedule_conflict",
                stage="student",
                conflicting_schedule_ids=[
                    str(schedule.id)
                    for schedule in self.schedules.overlapping_for_students(
                        item.academy_id,
                        overlapping_students,
                        item.starts_at,
                        item.ends_at,
                        item.exclude_schedule_id,
                    )
                ],
            )
        context.students = students

    def _validate_class_time(self, context: ScheduleValidationContext) -> None:
        item = context.candidate
        overlaps = self.schedules.overlapping_for_class(
            item.academy_id,
            item.class_id,
            item.starts_at,
            item.ends_at,
            item.exclude_schedule_id,
        )
        if overlaps:
            self._overlap(
                "Class already has an overlapping schedule.",
                "class_schedule_conflict",
                "time",
                overlaps,
            )

    def _validate_cross_branch(self, context: ScheduleValidationContext) -> None:
        item = context.candidate
        denied = [
            student
            for student in context.students
            if not self.cross_branch.student_can_access(student, item.branch_id)
        ]
        if denied:
            self._conflict(
                "A student does not have access to the schedule branch.",
                "student_cross_branch_denied",
                "cross_branch",
            )

    @staticmethod
    def _conflict(message: str, code: str, stage: str) -> None:
        raise SchedulingConflictError(message, code=code, stage=stage)

    @staticmethod
    def _overlap(message: str, code: str, stage: str, schedules: list) -> None:
        raise SchedulingConflictError(
            message,
            code=code,
            stage=stage,
            conflicting_schedule_ids=[str(schedule.id) for schedule in schedules],
        )
