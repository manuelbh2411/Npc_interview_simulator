import json

from openai import OpenAI, OpenAIError

from app.config import settings
from app.models.evaluation_models import EvaluationReport
from app.models.interview import Interview
from app.models.interview_models import InterviewMetadata, InterviewRecord, TranscriptMessage
from app.prompts.evaluation_prompt import EVALUATION_SYSTEM_PROMPT, build_evaluation_prompt


class EvaluationConfigurationError(RuntimeError):
    pass


class EvaluationServiceError(RuntimeError):
    pass


class OpenAIEvaluationService:
    """Adapta una entrevista guardada en SQL a la rubrica de evaluacion con GPT."""

    def evaluate_record(self, record: InterviewRecord) -> EvaluationReport:
        try:
            settings.require_openai()
        except RuntimeError as exc:
            raise EvaluationConfigurationError(str(exc)) from exc

        client = OpenAI(api_key=settings.openai_api_key)
        try:
            response = client.chat.completions.create(
                model=settings.openai_evaluation_model,
                messages=[
                    {"role": "system", "content": EVALUATION_SYSTEM_PROMPT},
                    {"role": "user", "content": build_evaluation_prompt(record)},
                ],
                temperature=0.2,
                response_format={"type": "json_object"},
            )
        except OpenAIError as exc:
            raise EvaluationServiceError(str(exc)) from exc

        content = response.choices[0].message.content or "{}"
        try:
            return EvaluationReport.model_validate(json.loads(content))
        except (json.JSONDecodeError, ValueError) as exc:
            raise EvaluationServiceError("OpenAI no devolvio un JSON de evaluacion valido") from exc

    def evaluate_interview(self, interview: Interview) -> EvaluationReport:
        transcript = [
            TranscriptMessage.model_validate(item)
            for item in (interview.transcript or [])
            if item.get("message")
        ]
        record = InterviewRecord(
            metadata=InterviewMetadata(
                session_id=interview.session_id,
                job_type=interview.job_type,
                interviewer_personality=interview.personality,
                status="stopped",
                started_at=interview.started_at,
                ended_at=interview.ended_at,
                duration_seconds=interview.duration_seconds,
            ),
            transcript=transcript,
        )
        return self.evaluate_record(record)
