from fastapi import APIRouter, Depends

from app.database import SessionLocal
from app.models.user import User
from app.schemas.report_schema import ReportRead
from app.security.jwt import get_current_user
from app.services.report_service import ReportService


router = APIRouter(tags=["Reports"])
report_service = ReportService()


@router.get("/reports", response_model=list[ReportRead])
async def list_reports(
    current_user: User = Depends(get_current_user),
) -> list[ReportRead]:
    """Lista todos los informes del usuario autenticado."""

    with SessionLocal() as db:
        return report_service.list_reports(db, current_user)


@router.get("/reports/{report_id}", response_model=ReportRead)
async def get_report(
    report_id: int,
    current_user: User = Depends(get_current_user),
) -> ReportRead:
    """Devuelve un informe propio por id."""

    with SessionLocal() as db:
        return report_service.get_report(db, current_user, report_id)


@router.get("/interviews/{interview_id}/report", response_model=ReportRead)
async def get_report_by_interview(
    interview_id: int,
    current_user: User = Depends(get_current_user),
) -> ReportRead:
    """Devuelve el informe asociado a una entrevista propia."""

    with SessionLocal() as db:
        return report_service.get_report_by_interview(db, current_user, interview_id)
