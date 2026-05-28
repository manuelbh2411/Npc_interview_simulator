from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


JobType = Literal["Ingeniería", "ADE", "Empresa", "Derecho", "Magisterio", "Marketing"]
PersonalityType = Literal["Amable", "Agresivo", "Técnico", "RRHH", "Startup informal"]
Speaker = Literal["interviewer", "candidate"]


class ElevenLabsSessionData(BaseModel):
    signed_url: str | None = None
    agent_id: str
    conversation_overrides: dict[str, Any]


class ElevenLabsSignedUrlResponse(BaseModel):
    signed_url: str
    agent_id: str


class TranscriptMessage(BaseModel):
    speaker: Speaker
    message: str
    timestamp: datetime


class InterviewMetadata(BaseModel):
    session_id: str
    job_type: str
    interviewer_personality: str
    candidate_name: str | None = None
    candidate_context: str | None = None
    status: str = "stopped"
    status_detail: str | None = None
    started_at: datetime
    ended_at: datetime | None = None
    duration_seconds: float | None = None


class InterviewRecord(BaseModel):
    metadata: InterviewMetadata
    transcript: list[TranscriptMessage] = Field(default_factory=list)
    report: dict[str, Any] | None = None


class HealthResponse(BaseModel):
    status: str


class InterviewOptionsResponse(BaseModel):
    jobs: list[str]
    personalities: list[str]
