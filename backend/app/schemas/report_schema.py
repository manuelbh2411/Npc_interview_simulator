from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ReportRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    interview_id: int
    overall_score: float = Field(ge=0, le=10)
    communication_score: float = Field(ge=0, le=10)
    coherence_score: float = Field(ge=0, le=10)
    job_fit_score: float = Field(ge=0, le=10)
    confidence_score: float = Field(ge=0, le=10)
    strengths: list[str]
    weaknesses: list[str]
    recommendations: list[str]
    summary_report: str
    final_feedback: str
    created_at: datetime
