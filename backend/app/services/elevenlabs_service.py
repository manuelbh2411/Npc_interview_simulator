from urllib.parse import urlencode

import httpx

from app.config import settings
from app.models.interview_models import ElevenLabsSessionData
from app.prompts import build_first_message, build_system_prompt
from app.utils.logger import setup_logger


logger = setup_logger(__name__)


class ElevenLabsConfigurationError(RuntimeError):
    pass


class ElevenLabsServiceError(RuntimeError):
    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        body: str | None = None,
        probable_cause: str | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.body = body
        self.probable_cause = probable_cause


class ElevenLabsService:
    """Prepara la sesion de ElevenLabs Conversational AI.

    El backend no genera las respuestas de la entrevista: pide una signed_url a
    ElevenLabs usando la API key del servidor y entrega esa URL al cliente junto
    con los overrides de personalidad.
    """

    def __init__(self, timeout_seconds: float = 15.0) -> None:
        self.timeout_seconds = timeout_seconds

    def build_conversation_overrides(
        self,
        job_type: str,
        personality: str,
        candidate_name: str | None = None,
        candidate_context: str | None = None,
    ) -> dict:
        prompt = build_system_prompt(
            job_type,
            personality,
            candidate_name=candidate_name,
            candidate_context=candidate_context,
        )
        first_message = build_first_message(
            personality,
            job=job_type,
            candidate_name=candidate_name,
        )

        return {
            "agent": {
                "prompt": {"prompt": prompt},
                "firstMessage": first_message,
                "language": "es",
            }
        }

    def _raise_response_error(self, response: httpx.Response, action: str) -> None:
        probable_cause = "Revisa ELEVENLABS_API_KEY y ELEVENLABS_AGENT_ID."
        if response.status_code == 401:
            probable_cause = "API key de ElevenLabs invalida o sin permisos."
        elif response.status_code == 404:
            probable_cause = "ELEVENLABS_AGENT_ID no existe o no pertenece a esta cuenta."
        elif response.status_code == 422:
            probable_cause = "agent_id invalido o parametros incorrectos para ElevenLabs."
        elif response.status_code >= 500:
            probable_cause = "ElevenLabs esta devolviendo un error temporal de servidor."

        body = response.text
        logger.error(
            "ElevenLabs %s failed status_code=%s body=%s probable_cause=%s",
            action,
            response.status_code,
            body,
            probable_cause,
        )
        raise ElevenLabsServiceError(
            f"Error de ElevenLabs al {action}",
            status_code=response.status_code,
            body=body,
            probable_cause=probable_cause,
        )

    def get_signed_url(self) -> str:
        try:
            settings.require_elevenlabs()
        except RuntimeError as exc:
            raise ElevenLabsConfigurationError(str(exc)) from exc

        params = {"agent_id": settings.elevenlabs_agent_id}
        url = f"{settings.elevenlabs_api_base}/get-signed-url?{urlencode(params)}"
        logger.info("Requesting ElevenLabs signed_url agent_id=%s", settings.elevenlabs_agent_id)
        response = httpx.get(
            url,
            headers={
                "xi-api-key": settings.elevenlabs_api_key or "",
                "Accept": "application/json",
            },
            timeout=self.timeout_seconds,
        )
        if response.status_code >= 400:
            self._raise_response_error(response, "generar signed_url")

        data = response.json()
        signed_url = data.get("signed_url") or data.get("signedUrl")
        if not signed_url:
            body = response.text
            logger.error("ElevenLabs signed_url missing body=%s", body)
            raise ElevenLabsServiceError(
                "ElevenLabs no devolvio signed_url",
                status_code=response.status_code,
                body=body,
                probable_cause="La respuesta de ElevenLabs no contiene signed_url.",
            )

        logger.info("ElevenLabs signed_url generated successfully")
        return signed_url

    def start_conversation(
        self,
        job_type: str,
        personality: str,
        candidate_name: str | None = None,
        candidate_context: str | None = None,
    ) -> tuple[ElevenLabsSessionData, str]:
        if not settings.elevenlabs_agent_id:
            raise ElevenLabsConfigurationError("Falta ELEVENLABS_AGENT_ID en backend/.env")

        signed_url = self.get_signed_url()
        overrides = self.build_conversation_overrides(
            job_type,
            personality,
            candidate_name=candidate_name,
            candidate_context=candidate_context,
        )
        return (
            ElevenLabsSessionData(
                signed_url=signed_url,
                agent_id=settings.elevenlabs_agent_id or "",
                conversation_overrides=overrides,
            ),
            overrides["agent"]["firstMessage"],
        )
