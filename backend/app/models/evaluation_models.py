from pydantic import BaseModel, Field


class EvaluationReport(BaseModel):
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
