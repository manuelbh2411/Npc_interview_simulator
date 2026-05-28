from datetime import UTC, datetime
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.interview import Interview as DbInterview
from app.models.report import Report as DbReport
from app.models.user import User
from app.schemas.interview_schema import (
    AuthenticatedInterviewStartRequest,
    AuthenticatedInterviewStartResponse,
    InterviewDeleteResponse,
    InterviewDetailResponse,
    InterviewEndResponse as DbInterviewEndResponse,
    InterviewMessageCreate,
    InterviewMessageResponse,
    InterviewSummaryResponse,
)
from app.schemas.report_schema import ReportRead
from app.services.elevenlabs_service import ElevenLabsService
from app.services.openai_evaluation_service import OpenAIEvaluationService


class UserInterviewService:
    """Casos de uso de entrevistas persistidas en base de datos por usuario."""

    def __init__(
        self,
        elevenlabs: ElevenLabsService | None = None,
        evaluator: OpenAIEvaluationService | None = None,
    ) -> None:
        self.elevenlabs = elevenlabs or ElevenLabsService()
        self.evaluator = evaluator or OpenAIEvaluationService()

    def _get_owned_interview(
        self,
        db: Session,
        interview_id: int,
        user: User,
    ) -> DbInterview:
        interview = db.get(DbInterview, interview_id)
        if not interview or interview.user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Entrevista no encontrada",
            )
        return interview

    @staticmethod
    def _duration_seconds(started_at: datetime, ended_at: datetime) -> int:
        if started_at.tzinfo is None:
            started_at = started_at.replace(tzinfo=UTC)
        if ended_at.tzinfo is None:
            ended_at = ended_at.replace(tzinfo=UTC)
        return max(0, int((ended_at - started_at).total_seconds()))

    @staticmethod
    def _summary(interview: DbInterview) -> InterviewSummaryResponse:
        return InterviewSummaryResponse(
            id=interview.id,
            title=interview.title,
            job_type=interview.job_type,
            personality=interview.personality,
            date=interview.created_at,
            duration_seconds=interview.duration_seconds,
            message_count=interview.message_count,
            status=interview.status,
            overall_score=interview.report.overall_score if interview.report else None,
            has_report=interview.report is not None,
        )

    def start_interview(
        self,
        db: Session,
        user: User,
        req: AuthenticatedInterviewStartRequest,
    ) -> AuthenticatedInterviewStartResponse:
        session_id = str(uuid4())
        title = req.title or f"{req.job_type} · {req.interviewer_personality}"
        interview = DbInterview(
            session_id=session_id,
            user_id=user.id,
            title=title,
            job_type=req.job_type,
            personality=req.interviewer_personality,
            status="in_progress",
            transcript=[],
        )
        db.add(interview)
        db.commit()
        db.refresh(interview)

        try:
            elevenlabs_data, initial_message = self.elevenlabs.start_conversation(
                job_type=req.job_type,
                personality=req.interviewer_personality,
                candidate_name=req.candidate_name or user.name,
                candidate_context=req.candidate_context,
            )
        except Exception:
            interview.status = "failed"
            db.commit()
            raise

        return AuthenticatedInterviewStartResponse(
            id=interview.id,
            session_id=interview.session_id,
            title=interview.title,
            job_type=interview.job_type,
            personality=interview.personality,
            status=interview.status,
            elevenlabs_session_data=elevenlabs_data,
            initial_message=initial_message,
        )

    def add_message(
        self,
        db: Session,
        user: User,
        interview_id: int,
        req: InterviewMessageCreate,
    ) -> InterviewMessageResponse:
        interview = self._get_owned_interview(db, interview_id, user)
        if interview.status not in {"in_progress", "completed"}:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"No se pueden guardar mensajes en estado {interview.status}",
            )

        timestamp = req.timestamp or datetime.now(UTC)
        transcript = list(interview.transcript or [])
        transcript.append(
            {
                "speaker": req.speaker,
                "message": req.message.strip(),
                "timestamp": timestamp.isoformat(),
            }
        )
        interview.transcript = transcript
        interview.message_count = len(transcript)
        db.commit()
        db.refresh(interview)

        return InterviewMessageResponse(
            interview_id=interview.id,
            stored=True,
            message_count=interview.message_count,
        )

    def end_interview(
        self,
        db: Session,
        user: User,
        interview_id: int,
    ) -> DbInterviewEndResponse:
        interview = self._get_owned_interview(db, interview_id, user)
        ended_at = datetime.now(UTC)
        interview.ended_at = ended_at
        interview.duration_seconds = self._duration_seconds(interview.started_at, ended_at)
        interview.message_count = len(interview.transcript or [])

        if interview.report:
            interview.status = "completed"
            db.commit()
            return DbInterviewEndResponse(
                interview_id=interview.id,
                status=interview.status,
                duration_seconds=interview.duration_seconds,
                message_count=interview.message_count,
                report=ReportRead.model_validate(interview.report),
            )

        try:
            evaluation = self.evaluator.evaluate_interview(interview)
        except Exception:
            interview.status = "failed"
            db.commit()
            raise

        report = DbReport(
            interview_id=interview.id,
            overall_score=evaluation.overall_score,
            communication_score=evaluation.communication_score,
            coherence_score=evaluation.coherence_score,
            job_fit_score=evaluation.job_fit_score,
            confidence_score=evaluation.confidence_score,
            strengths=evaluation.strengths,
            weaknesses=evaluation.weaknesses,
            recommendations=evaluation.recommendations,
            summary_report=evaluation.summary_report,
            final_feedback=evaluation.final_feedback,
        )
        interview.status = "completed"
        db.add(report)
        db.commit()
        db.refresh(report)
        interview.report_id = report.id
        db.commit()
        db.refresh(interview)

        return DbInterviewEndResponse(
            interview_id=interview.id,
            status=interview.status,
            duration_seconds=interview.duration_seconds,
            message_count=interview.message_count,
            report=ReportRead.model_validate(report),
        )

    def list_interviews(self, db: Session, user: User) -> list[InterviewSummaryResponse]:
        interviews = db.scalars(
            select(DbInterview)
            .where(DbInterview.user_id == user.id)
            .order_by(DbInterview.created_at.desc())
        ).all()
        return [self._summary(interview) for interview in interviews]

    def get_interview(
        self,
        db: Session,
        user: User,
        interview_id: int,
    ) -> InterviewDetailResponse:
        interview = self._get_owned_interview(db, interview_id, user)
        return InterviewDetailResponse.model_validate(interview)

    def delete_interview(
        self,
        db: Session,
        user: User,
        interview_id: int,
    ) -> InterviewDeleteResponse:
        interview = self._get_owned_interview(db, interview_id, user)
        db.delete(interview)
        db.commit()
        return InterviewDeleteResponse(interview_id=interview_id, deleted=True)
