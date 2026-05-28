from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.interview import Interview
from app.models.report import Report
from app.models.user import User
from app.schemas.report_schema import ReportRead


class ReportService:
    """Consulta informes respetando la propiedad de cada usuario."""

    def list_reports(self, db: Session, user: User) -> list[ReportRead]:
        reports = db.scalars(
            select(Report)
            .join(Interview, Report.interview_id == Interview.id)
            .where(Interview.user_id == user.id)
            .order_by(Report.created_at.desc())
        ).all()
        return [ReportRead.model_validate(report) for report in reports]

    def get_report(self, db: Session, user: User, report_id: int) -> ReportRead:
        report = db.scalar(
            select(Report)
            .join(Interview, Report.interview_id == Interview.id)
            .where(Report.id == report_id, Interview.user_id == user.id)
        )
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Informe no encontrado",
            )
        return ReportRead.model_validate(report)

    def get_report_by_interview(
        self,
        db: Session,
        user: User,
        interview_id: int,
    ) -> ReportRead:
        report = db.scalar(
            select(Report)
            .join(Interview, Report.interview_id == Interview.id)
            .where(Interview.id == interview_id, Interview.user_id == user.id)
        )
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="La entrevista no tiene informe generado",
            )
        return ReportRead.model_validate(report)
