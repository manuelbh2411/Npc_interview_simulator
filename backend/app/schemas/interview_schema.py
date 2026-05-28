from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.models.interview_models import ElevenLabsSessionData
from app.schemas.report_schema import ReportRead


JobType = Literal["Ingeniería", "ADE", "Empresa", "Derecho", "Magisterio", "Marketing"]
PersonalityType = Literal["Amable", "Agresivo", "Técnico", "RRHH", "Startup informal"]
InterviewLifecycleStatus = Literal["in_progress", "completed", "cancelled", "failed"]
SpeakerType = Literal["interviewer", "candidate"]


class AuthenticatedInterviewStartRequest(BaseModel):
    title: str | None = Field(default=None, max_length=180)
    job_type: JobType
    interviewer_personality: PersonalityType
    candidate_name: str | None = Field(default=None, max_length=80)
    candidate_context: str | None = Field(default=None, max_length=1000)


class AuthenticatedInterviewStartResponse(BaseModel):
    id: int
    session_id: str
    title: str
    job_type: str
    personality: str
    status: InterviewLifecycleStatus
    elevenlabs_session_data: ElevenLabsSessionData
    initial_message: str


class InterviewMessageCreate(BaseModel):
    speaker: SpeakerType
    message: str = Field(min_length=1, max_length=5000)
    timestamp: datetime | None = None


class InterviewMessageResponse(BaseModel):
    interview_id: int
    stored: bool
    message_count: int


class TranscriptItem(BaseModel):
    speaker: SpeakerType
    message: str
    timestamp: datetime


class InterviewSummaryResponse(BaseModel):
    id: int
    title: str
    job_type: str
    personality: str
    date: datetime
    duration_seconds: int | None
    message_count: int
    status: str
    overall_score: float | None
    has_report: bool


class InterviewDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: str
    title: str
    job_type: str
    personality: str
    status: str
    duration_seconds: int | None
    message_count: int
    transcript: list[dict[str, Any]]
    created_at: datetime
    started_at: datetime
    ended_at: datetime | None
    report: ReportRead | None = None


class InterviewEndResponse(BaseModel):
    interview_id: int
    status: str
    duration_seconds: int | None
    message_count: int
    report: ReportRead


class InterviewDeleteResponse(BaseModel):
    interview_id: int
    deleted: bool
