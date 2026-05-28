from fastapi import APIRouter, Depends, HTTPException

from app.database import SessionLocal
from app.models.user import User
from app.schemas.interview_schema import (
    AuthenticatedInterviewStartRequest,
    AuthenticatedInterviewStartResponse,
    InterviewDeleteResponse,
    InterviewDetailResponse,
    InterviewEndResponse,
    InterviewMessageCreate,
    InterviewMessageResponse,
    InterviewSummaryResponse,
)
from app.security.jwt import get_current_user
from app.services.elevenlabs_service import (
    ElevenLabsConfigurationError,
    ElevenLabsServiceError,
)
from app.services.openai_evaluation_service import (
    EvaluationConfigurationError,
    EvaluationServiceError,
)
from app.services.interview_service import UserInterviewService


router = APIRouter(prefix="/interviews", tags=["Interviews"])
interview_service = UserInterviewService()


@router.post("/start", response_model=AuthenticatedInterviewStartResponse)
async def start_interview(
    payload: AuthenticatedInterviewStartRequest,
    current_user: User = Depends(get_current_user),
) -> AuthenticatedInterviewStartResponse:
    """Crea una entrevista privada del usuario y devuelve la sesion de ElevenLabs."""

    try:
        with SessionLocal() as db:
            return interview_service.start_interview(db, current_user, payload)
    except ElevenLabsConfigurationError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except ElevenLabsServiceError as exc:
        raise HTTPException(
            status_code=502,
            detail={
                "message": str(exc),
                "status_code": exc.status_code,
                "body": exc.body,
                "probable_cause": exc.probable_cause,
            },
        ) from exc


@router.post("/{interview_id}/message", response_model=InterviewMessageResponse)
async def store_message(
    interview_id: int,
    payload: InterviewMessageCreate,
    current_user: User = Depends(get_current_user),
) -> InterviewMessageResponse:
    """Guarda un mensaje de entrevistador o candidato en la transcripcion."""

    with SessionLocal() as db:
        return interview_service.add_message(db, current_user, interview_id, payload)


@router.post("/{interview_id}/end", response_model=InterviewEndResponse)
async def end_interview(
    interview_id: int,
    current_user: User = Depends(get_current_user),
) -> InterviewEndResponse:
    """Finaliza la entrevista, calcula duracion, evalua con GPT y guarda informe."""

    try:
        with SessionLocal() as db:
            return interview_service.end_interview(db, current_user, interview_id)
    except EvaluationConfigurationError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except EvaluationServiceError as exc:
        raise HTTPException(status_code=502, detail=f"Error de OpenAI: {exc}") from exc


@router.get("", response_model=list[InterviewSummaryResponse])
async def list_interviews(
    current_user: User = Depends(get_current_user),
) -> list[InterviewSummaryResponse]:
    """Lista el historial del usuario autenticado para el panel personal."""

    with SessionLocal() as db:
        return interview_service.list_interviews(db, current_user)


@router.get("/{interview_id}", response_model=InterviewDetailResponse)
async def get_interview(
    interview_id: int,
    current_user: User = Depends(get_current_user),
) -> InterviewDetailResponse:
    """Devuelve una entrevista propia con transcripcion e informe si existe."""

    with SessionLocal() as db:
        return interview_service.get_interview(db, current_user, interview_id)


@router.delete("/{interview_id}", response_model=InterviewDeleteResponse)
async def delete_interview(
    interview_id: int,
    current_user: User = Depends(get_current_user),
) -> InterviewDeleteResponse:
    """Borra solo entrevistas pertenecientes al usuario autenticado."""

    with SessionLocal() as db:
        return interview_service.delete_interview(db, current_user, interview_id)
