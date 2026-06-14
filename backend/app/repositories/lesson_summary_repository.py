from uuid import UUID

from sqlalchemy import select

from app.extensions import db
from app.models.lesson_summary import LessonSummary
from app.models.lesson_summary_edit_request import LessonSummaryEditRequest
from app.repositories.base import BaseRepository


class LessonSummaryRepository(BaseRepository[LessonSummary]):
    def __init__(self) -> None:
        super().__init__(LessonSummary)

    def get_for_session(self, session_id: UUID) -> LessonSummary | None:
        return db.session.scalar(
            select(LessonSummary).where(LessonSummary.session_id == session_id)
        )

    def get_scoped(
        self,
        academy_id: UUID,
        branch_id: UUID,
        summary_id: UUID,
    ) -> LessonSummary | None:
        return db.session.scalar(
            select(LessonSummary).where(
                LessonSummary.id == summary_id,
                LessonSummary.academy_id == academy_id,
                LessonSummary.branch_id == branch_id,
            )
        )


class LessonSummaryEditRequestRepository(
    BaseRepository[LessonSummaryEditRequest]
):
    def __init__(self) -> None:
        super().__init__(LessonSummaryEditRequest)

    def get_scoped_for_update(
        self,
        academy_id: UUID,
        branch_id: UUID,
        request_id: UUID,
    ) -> LessonSummaryEditRequest | None:
        return db.session.scalar(
            select(LessonSummaryEditRequest)
            .where(
                LessonSummaryEditRequest.id == request_id,
                LessonSummaryEditRequest.academy_id == academy_id,
                LessonSummaryEditRequest.branch_id == branch_id,
            )
            .with_for_update()
        )

    def pending_for_summary(
        self,
        summary_id: UUID,
    ) -> LessonSummaryEditRequest | None:
        return db.session.scalar(
            select(LessonSummaryEditRequest).where(
                LessonSummaryEditRequest.lesson_summary_id == summary_id,
                LessonSummaryEditRequest.status == "pending",
            )
        )
