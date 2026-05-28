from app.models.interview_models import InterviewRecord


EVALUATION_SYSTEM_PROMPT = """
Eres un evaluador experto de entrevistas laborales para un TFG sobre NPCs con LLMs.
Tu trabajo no es entrevistar: solo analizar una transcripcion ya terminada.
Devuelve exclusivamente JSON valido, sin markdown y sin texto adicional.
""".strip()


def build_evaluation_prompt(record: InterviewRecord) -> str:
    transcript = "\n".join(
        f"[{message.timestamp.isoformat()}] {message.speaker}: {message.message}"
        for message in record.transcript
    )

    return f"""
Analiza esta entrevista laboral y genera una evaluacion estructurada.

Metadatos:
- session_id: {record.metadata.session_id}
- tipo_entrevista: {record.metadata.job_type}
- personalidad_entrevistador: {record.metadata.interviewer_personality}
- candidato: {record.metadata.candidate_name or "No indicado"}
- duracion_segundos: {record.metadata.duration_seconds}

Rubrica obligatoria:
- Claridad comunicativa.
- Coherencia de respuestas.
- Seguridad y confianza.
- Adecuacion al puesto.
- Capacidad de argumentacion.
- Estructura de las respuestas.
- Ejemplos concretos aportados.
- Capacidad de autocritica.
- Profesionalidad.
- Puntos fuertes.
- Puntos debiles.
- Recomendaciones de mejora.

Transcripcion:
{transcript or "No hay transcripcion suficiente."}

Devuelve JSON con exactamente esta forma:
{{
  "overall_score": 0-10,
  "communication_score": 0-10,
  "coherence_score": 0-10,
  "job_fit_score": 0-10,
  "confidence_score": 0-10,
  "strengths": ["..."],
  "weaknesses": ["..."],
  "recommendations": ["..."],
  "summary_report": "...",
  "final_feedback": "..."
}}
""".strip()
