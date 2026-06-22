from datetime import date, datetime, time, timezone
from uuid import UUID

from sqlalchemy import func, select

from app.common.cache import cached_value
from app.common.errors import NotFoundError
from app.domain.attendance_status import AttendanceStatus
from app.domain.financial_status import InvoiceStatus, PaymentStatus
from app.domain.scheduling_status import SessionStatus
from app.extensions import db
from app.models.academic_invoice import AcademicInvoice
from app.models.academic_payment import AcademicPayment
from app.models.attendance import Attendance
from app.models.branch import Branch
from app.models.class_session import ClassSession
from app.models.notification import Notification
from app.models.parent import Parent
from app.models.parent_student import ParentStudent
from app.models.schedule import Schedule
from app.models.student import Student
from app.models.teacher_branch import TeacherBranch
from app.permissions.constants import Permission
from app.permissions.context import AuthorizationTarget, Principal
from app.repositories.academy_repository import AcademyRepository
from app.repositories.branch_repository import BranchRepository
from app.services.authorization_service import AuthorizationService


class AnalyticsService:
    def __init__(
        self,
        academy_repository: AcademyRepository | None = None,
        branch_repository: BranchRepository | None = None,
    ) -> None:
        self.academy_repository = academy_repository or AcademyRepository()
        self.branch_repository = branch_repository or BranchRepository()

    def academy_overview(
        self,
        principal: Principal,
        academy_id: UUID,
        *,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> dict[str, object]:
        academy = self.academy_repository.get_by_id(academy_id)
        if academy is None:
            raise NotFoundError("Academy")
        AuthorizationService.require(
            principal,
            Permission.REPORT_VIEW,
            AuthorizationTarget(academy_id=academy.id),
        )
        cache_key = self._cache_key("academy_overview", academy.id, start_date, end_date)
        return cached_value(
            cache_key,
            lambda: self._academy_overview_payload(
                academy.id,
                start_date=start_date,
                end_date=end_date,
            ),
        )[0]

    def branch_kpi(
        self,
        principal: Principal,
        branch_id: UUID,
        *,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> dict[str, object]:
        branch = self.branch_repository.get_by_id(branch_id)
        if branch is None:
            raise NotFoundError("Branch")
        AuthorizationService.require(
            principal,
            Permission.REPORT_VIEW,
            AuthorizationTarget(
                academy_id=branch.academy_id,
                branch_id=branch.id,
            ),
        )
        cache_key = self._cache_key("branch_kpi", branch.id, start_date, end_date)
        return cached_value(
            cache_key,
            lambda: self._branch_kpi(branch, start_date=start_date, end_date=end_date),
        )[0]

    def cached_branch_kpi(
        self,
        principal: Principal,
        branch_id: UUID,
        *,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> tuple[dict[str, object], bool]:
        branch = self.branch_repository.get_by_id(branch_id)
        if branch is None:
            raise NotFoundError("Branch")
        AuthorizationService.require(
            principal,
            Permission.REPORT_VIEW,
            AuthorizationTarget(
                academy_id=branch.academy_id,
                branch_id=branch.id,
            ),
        )
        return cached_value(
            self._cache_key("branch_kpi", branch.id, start_date, end_date),
            lambda: self._branch_kpi(branch, start_date=start_date, end_date=end_date),
        )

    def cached_academy_overview(
        self,
        principal: Principal,
        academy_id: UUID,
        *,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> tuple[dict[str, object], bool]:
        academy = self.academy_repository.get_by_id(academy_id)
        if academy is None:
            raise NotFoundError("Academy")
        AuthorizationService.require(
            principal,
            Permission.REPORT_VIEW,
            AuthorizationTarget(academy_id=academy.id),
        )
        return cached_value(
            self._cache_key("academy_overview", academy.id, start_date, end_date),
            lambda: self._academy_overview_payload(
                academy.id,
                start_date=start_date,
                end_date=end_date,
            ),
        )

    def _academy_overview_payload(
        self,
        academy_id: UUID,
        *,
        start_date: date | None,
        end_date: date | None,
    ) -> dict[str, object]:
        branches = self.branch_repository.list_for_academy(academy_id)
        branch_payloads = [
            self._branch_kpi(branch, start_date=start_date, end_date=end_date)
            for branch in branches
        ]
        return {
            "academy_id": str(academy_id),
            "period": self._serialize_period(start_date, end_date),
            "branches": branch_payloads,
            "totals": self._academy_totals_from_branches(branch_payloads),
        }

    def _branch_kpi(
        self,
        branch: Branch,
        *,
        start_date: date | None,
        end_date: date | None,
    ) -> dict[str, object]:
        attendance = self._attendance_metrics(
            academy_id=branch.academy_id,
            branch_id=branch.id,
            start_date=start_date,
            end_date=end_date,
        )
        revenue = self._revenue_metrics(
            academy_id=branch.academy_id,
            branch_id=branch.id,
            start_date=start_date,
            end_date=end_date,
        )
        scheduled_sessions = self._session_count(
            branch.academy_id,
            branch.id,
            start_date=start_date,
            end_date=end_date,
        )
        completed_sessions = self._session_count(
            branch.academy_id,
            branch.id,
            status=SessionStatus.COMPLETED,
            start_date=start_date,
            end_date=end_date,
        )
        cancelled_sessions = self._session_count(
            branch.academy_id,
            branch.id,
            status=SessionStatus.CANCELLED,
            start_date=start_date,
            end_date=end_date,
        )
        rescheduled_sessions = self._session_count(
            branch.academy_id,
            branch.id,
            status=SessionStatus.RESCHEDULED,
            start_date=start_date,
            end_date=end_date,
        )
        stable_sessions = max(
            scheduled_sessions - cancelled_sessions - rescheduled_sessions,
            0,
        )
        return {
            "academy_id": str(branch.academy_id),
            "branch_id": str(branch.id),
            "branch_name": branch.name,
            "period": self._serialize_period(start_date, end_date),
            "active_students": self.branch_repository.active_student_count(
                branch.academy_id,
                branch.id,
            ),
            "active_teachers": self.branch_repository.active_teacher_count(
                branch.academy_id,
                branch.id,
            ),
            "scheduled_sessions": scheduled_sessions,
            "completed_sessions": completed_sessions,
            "completion_rate": self._ratio(completed_sessions, scheduled_sessions),
            "cancelled_sessions": cancelled_sessions,
            "rescheduled_sessions": rescheduled_sessions,
            "stability_rate": self._ratio(stable_sessions, scheduled_sessions),
            "attendance": attendance,
            "revenue": revenue,
            "teacher_workload": self._teacher_workload(
                branch.academy_id,
                branch.id,
                start_date=start_date,
                end_date=end_date,
            ),
            "parent_engagement": self._parent_engagement(
                branch.academy_id,
                branch.id,
                start_date=start_date,
                end_date=end_date,
            ),
        }

    def _academy_totals_from_branches(self, branches: list[dict[str, object]]) -> dict[str, object]:
        if not branches:
            return {
                "active_students": 0,
                "active_teachers": 0,
                "scheduled_sessions": 0,
                "completed_sessions": 0,
                "cancelled_sessions": 0,
                "rescheduled_sessions": 0,
                "completion_rate": 0.0,
                "attendance_rate": 0.0,
                "stability_rate": 0.0,
                "teacher_workload": {
                    "assigned_teachers": 0,
                    "teachers_with_sessions": 0,
                    "total_sessions": 0,
                    "max_sessions_per_teacher": 0,
                    "average_sessions_per_teacher": 0.0,
                },
                "parent_engagement": {
                    "linked_students": 0,
                    "notifications_sent": 0,
                },
                "issued_revenue_minor": 0,
                "collected_revenue_minor": 0,
                "outstanding_revenue_minor": 0,
            }
        active_students = sum(item["active_students"] for item in branches)
        active_teachers = sum(item["active_teachers"] for item in branches)
        scheduled_sessions = sum(item["scheduled_sessions"] for item in branches)
        completed_sessions = sum(item["completed_sessions"] for item in branches)
        cancelled_sessions = sum(item["cancelled_sessions"] for item in branches)
        rescheduled_sessions = sum(item["rescheduled_sessions"] for item in branches)
        stable_sessions = max(
            scheduled_sessions - cancelled_sessions - rescheduled_sessions,
            0,
        )
        attendance_records = sum(
            item["attendance"]["total_records"] for item in branches
        )
        attended_records = sum(
            item["attendance"]["attended_records"] for item in branches
        )
        teacher_total_sessions = sum(
            item["teacher_workload"]["total_sessions"] for item in branches
        )
        teachers_with_sessions = sum(
            item["teacher_workload"]["teachers_with_sessions"] for item in branches
        )
        linked_students = sum(
            item["parent_engagement"]["linked_students"] for item in branches
        )
        notifications_sent = sum(
            item["parent_engagement"]["notifications_sent"] for item in branches
        )
        return {
            "active_students": active_students,
            "active_teachers": active_teachers,
            "scheduled_sessions": scheduled_sessions,
            "completed_sessions": completed_sessions,
            "cancelled_sessions": cancelled_sessions,
            "rescheduled_sessions": rescheduled_sessions,
            "completion_rate": self._ratio(
                completed_sessions,
                scheduled_sessions,
            ),
            "attendance_rate": self._ratio(attended_records, attendance_records),
            "stability_rate": self._ratio(stable_sessions, scheduled_sessions),
            "teacher_workload": {
                "assigned_teachers": active_teachers,
                "teachers_with_sessions": teachers_with_sessions,
                "total_sessions": teacher_total_sessions,
                "max_sessions_per_teacher": max(
                    (
                        item["teacher_workload"]["max_sessions_per_teacher"]
                        for item in branches
                    ),
                    default=0,
                ),
                "average_sessions_per_teacher": self._ratio(
                    teacher_total_sessions,
                    teachers_with_sessions,
                ),
            },
            "parent_engagement": {
                "linked_students": linked_students,
                "notifications_sent": notifications_sent,
            },
            "issued_revenue_minor": sum(
                item["revenue"]["issued_revenue_minor"] for item in branches
            ),
            "collected_revenue_minor": sum(
                item["revenue"]["collected_revenue_minor"] for item in branches
            ),
            "outstanding_revenue_minor": sum(
                item["revenue"]["outstanding_revenue_minor"] for item in branches
            ),
        }

    def _session_count(
        self,
        academy_id: UUID,
        branch_id: UUID,
        *,
        status: str | None = None,
        start_date: date | None,
        end_date: date | None,
    ) -> int:
        query = (
            select(func.count(ClassSession.id))
            .join(Schedule, Schedule.id == ClassSession.schedule_id)
            .where(
                ClassSession.academy_id == academy_id,
                ClassSession.branch_id == branch_id,
            )
        )
        if status is not None:
            query = query.where(ClassSession.status == status)
        query = self._apply_schedule_period(query, start_date, end_date)
        return db.session.scalar(query) or 0

    def _attendance_metrics(
        self,
        *,
        academy_id: UUID,
        branch_id: UUID,
        start_date: date | None,
        end_date: date | None,
    ) -> dict[str, object]:
        query = (
            select(Attendance.attendance_status, func.count(Attendance.id))
            .join(Schedule, Schedule.id == Attendance.schedule_id)
            .where(
                Attendance.academy_id == academy_id,
                Attendance.branch_id == branch_id,
            )
            .group_by(Attendance.attendance_status)
        )
        query = self._apply_schedule_period(query, start_date, end_date)
        by_status = {
            status: count
            for status, count in db.session.execute(query).all()
        }
        total_records = sum(by_status.values())
        attended_records = sum(
            by_status.get(status, 0)
            for status in (
                AttendanceStatus.PRESENT,
                AttendanceStatus.LATE,
                AttendanceStatus.ONLINE,
            )
        )
        return {
            "total_records": total_records,
            "attended_records": attended_records,
            "attendance_rate": self._ratio(attended_records, total_records),
            "by_status": {
                status.value: by_status.get(status.value, 0)
                for status in AttendanceStatus
            },
        }

    def _revenue_metrics(
        self,
        *,
        academy_id: UUID,
        branch_id: UUID,
        start_date: date | None,
        end_date: date | None,
    ) -> dict[str, object]:
        invoice_query = select(
            func.coalesce(func.sum(AcademicInvoice.amount_minor), 0),
            func.coalesce(func.sum(AcademicInvoice.paid_minor), 0),
        ).where(
            AcademicInvoice.academy_id == academy_id,
            AcademicInvoice.branch_id == branch_id,
            AcademicInvoice.status != InvoiceStatus.CANCELLED,
        )
        if start_date is not None:
            invoice_query = invoice_query.where(
                AcademicInvoice.due_date >= start_date
            )
        if end_date is not None:
            invoice_query = invoice_query.where(AcademicInvoice.due_date <= end_date)
        issued_minor, paid_minor = db.session.execute(invoice_query).one()

        payment_query = select(
            func.coalesce(func.sum(AcademicPayment.amount_minor), 0)
        ).where(
            AcademicPayment.academy_id == academy_id,
            AcademicPayment.branch_id == branch_id,
            AcademicPayment.status == PaymentStatus.CONFIRMED,
        )
        if start_date is not None:
            payment_query = payment_query.where(
                AcademicPayment.submitted_at >= self._start_of_day(start_date)
            )
        if end_date is not None:
            payment_query = payment_query.where(
                AcademicPayment.submitted_at <= self._end_of_day(end_date)
            )
        collected_minor = db.session.scalar(payment_query) or 0
        return {
            "issued_revenue_minor": int(issued_minor or 0),
            "recorded_paid_minor": int(paid_minor or 0),
            "collected_revenue_minor": int(collected_minor or 0),
            "outstanding_revenue_minor": max(
                int(issued_minor or 0) - int(paid_minor or 0),
                0,
            ),
        }

    def _teacher_workload(
        self,
        academy_id: UUID,
        branch_id: UUID,
        *,
        start_date: date | None,
        end_date: date | None,
    ) -> dict[str, object]:
        query = (
            select(Schedule.teacher_id, func.count(Schedule.id))
            .where(
                Schedule.academy_id == academy_id,
                Schedule.branch_id == branch_id,
                Schedule.status != "cancelled",
            )
            .group_by(Schedule.teacher_id)
        )
        query = self._apply_schedule_period(query, start_date, end_date)
        rows = db.session.execute(query).all()
        session_counts = [count for _, count in rows]
        return {
            "assigned_teachers": self.branch_repository.active_teacher_count(
                academy_id,
                branch_id,
            ),
            "teachers_with_sessions": len(rows),
            "total_sessions": sum(session_counts),
            "max_sessions_per_teacher": max(session_counts, default=0),
            "average_sessions_per_teacher": self._ratio(
                sum(session_counts),
                len(rows),
            ),
        }

    def _parent_engagement(
        self,
        academy_id: UUID,
        branch_id: UUID,
        *,
        start_date: date | None,
        end_date: date | None,
    ) -> dict[str, object]:
        linked_students = db.session.scalar(
            select(func.count(func.distinct(ParentStudent.student_id)))
            .join(Student, Student.id == ParentStudent.student_id)
            .where(
                ParentStudent.academy_id == academy_id,
                ParentStudent.relationship_status == "active",
                Student.academy_id == academy_id,
                Student.home_branch_id == branch_id,
                Student.status == "active",
            )
        ) or 0
        notification_query = (
            select(func.count(func.distinct(Notification.id)))
            .join(Parent, Parent.user_id == Notification.recipient_user_id)
            .join(ParentStudent, ParentStudent.parent_id == Parent.id)
            .join(Student, Student.id == ParentStudent.student_id)
            .where(
                Notification.academy_id == academy_id,
                Parent.academy_id == academy_id,
                Parent.status == "active",
                ParentStudent.academy_id == academy_id,
                ParentStudent.relationship_status == "active",
                Student.academy_id == academy_id,
                Student.home_branch_id == branch_id,
                Student.status == "active",
            )
        )
        if start_date is not None:
            notification_query = notification_query.where(
                Notification.created_at >= self._start_of_day(start_date)
            )
        if end_date is not None:
            notification_query = notification_query.where(
                Notification.created_at <= self._end_of_day(end_date)
            )
        notification_count = db.session.scalar(notification_query) or 0
        return {
            "linked_students": linked_students,
            "notifications_sent": notification_count,
        }

    def _apply_schedule_period(self, query, start_date, end_date):
        if start_date is not None:
            query = query.where(Schedule.starts_at >= self._start_of_day(start_date))
        if end_date is not None:
            query = query.where(Schedule.starts_at <= self._end_of_day(end_date))
        return query

    @staticmethod
    def _serialize_period(
        start_date: date | None,
        end_date: date | None,
    ) -> dict[str, str | None]:
        return {
            "from": start_date.isoformat() if start_date else None,
            "to": end_date.isoformat() if end_date else None,
        }

    @staticmethod
    def _start_of_day(value: date) -> datetime:
        return datetime.combine(value, time.min, tzinfo=timezone.utc)

    @staticmethod
    def _end_of_day(value: date) -> datetime:
        return datetime.combine(value, time.max, tzinfo=timezone.utc)

    @staticmethod
    def _ratio(numerator: int, denominator: int) -> float:
        if denominator == 0:
            return 0.0
        return round(numerator / denominator, 4)

    @staticmethod
    def _cache_key(
        namespace: str,
        entity_id: UUID,
        start_date: date | None,
        end_date: date | None,
    ) -> str:
        return (
            f"analytics:{namespace}:{entity_id}:"
            f"{start_date.isoformat() if start_date else 'none'}:"
            f"{end_date.isoformat() if end_date else 'none'}"
        )
