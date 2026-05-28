import mimetypes

from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db
from app.models import HealthResponse, ElevenLabsSignedUrlResponse, InterviewOptionsResponse
from app.prompts import JOBS, PERSONALITIES
from app.routes.auth_routes import router as auth_router
from app.routes.game_routes import router as game_router
from app.routes.interview_routes import router as authenticated_interview_router
from app.routes.report_routes import router as report_router
from app.services.elevenlabs_service import (
    ElevenLabsConfigurationError,
    ElevenLabsService,
    ElevenLabsServiceError,
)
from app.utils.logger import setup_logger


logger = setup_logger()
app = FastAPI(title=settings.app_name, version=settings.api_version)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()
app.include_router(auth_router)
app.include_router(game_router)
app.include_router(authenticated_interview_router)
app.include_router(report_router)

elevenlabs_service = ElevenLabsService()


def static_response(relative_path: str) -> Response:
    """Sirve la pequena UI local de prueba desde backend/app/static."""

    file_path = (settings.static_dir / relative_path).resolve()
    static_root = settings.static_dir.resolve()
    if not file_path.is_relative_to(static_root) or not file_path.is_file():
        raise HTTPException(status_code=404, detail="Archivo estatico no encontrado")

    media_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
    return Response(content=file_path.read_bytes(), media_type=media_type)


@app.get("/", include_in_schema=False)
async def landing_ui() -> Response:
    return static_response("index.html")


@app.get("/setup", include_in_schema=False)
async def setup_ui() -> Response:
    return static_response("setup.html")


@app.get("/dashboard", include_in_schema=False)
async def dashboard_ui() -> Response:
    return static_response("dashboard.html")


@app.get("/realtime", include_in_schema=False)
async def realtime_ui() -> Response:
    return static_response("agent.html")


@app.get("/interview", include_in_schema=False)
async def interview_ui() -> Response:
    return static_response("agent.html")


@app.get("/static/{file_path:path}", include_in_schema=False)
async def static_asset(file_path: str) -> Response:
    return static_response(file_path)


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok")


@app.get("/options", response_model=InterviewOptionsResponse)
async def options() -> InterviewOptionsResponse:
    return InterviewOptionsResponse(jobs=JOBS, personalities=PERSONALITIES)


@app.get("/elevenlabs/signed-url", response_model=ElevenLabsSignedUrlResponse)
async def elevenlabs_signed_url() -> ElevenLabsSignedUrlResponse:
    """Devuelve una signed_url de ElevenLabs sin exponer la API key."""

    try:
        signed_url = elevenlabs_service.get_signed_url()
        return ElevenLabsSignedUrlResponse(
            signed_url=signed_url,
            agent_id=settings.elevenlabs_agent_id or "",
        )
    except ElevenLabsConfigurationError as exc:
        logger.error("ElevenLabs configuration error: %s", exc)
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
