from functools import lru_cache
from pathlib import Path
import os

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent
BACKEND_DIR = BASE_DIR.parent
ENV_FILE = BACKEND_DIR / ".env"

load_dotenv(dotenv_path=ENV_FILE)


class Settings:
    """Configuracion centralizada del backend.

    Las claves se cargan desde backend/.env para no escribir secretos en codigo.
    """

    app_name: str = "TFG NPC Interview Simulator"
    api_version: str = "1.0.0"

    elevenlabs_api_key: str | None
    elevenlabs_agent_id: str | None
    elevenlabs_api_base: str

    openai_api_key: str | None
    openai_evaluation_model: str

    database_url: str
    jwt_secret_key: str
    jwt_algorithm: str
    access_token_expire_minutes: int
    cors_origins: list[str]

    data_dir: Path
    static_dir: Path
    database_path: Path

    def __init__(self) -> None:
        self.elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
        self.elevenlabs_agent_id = os.getenv("ELEVENLABS_AGENT_ID")
        self.elevenlabs_api_base = os.getenv(
            "ELEVENLABS_API_BASE",
            "https://api.elevenlabs.io/v1/convai/conversation",
        )

        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.openai_evaluation_model = os.getenv("OPENAI_EVALUATION_MODEL", "gpt-4.1-mini")

        self.data_dir = BASE_DIR / "data"
        self.static_dir = BASE_DIR / "static"
        self.database_path = self.data_dir / "tfg_interviews.db"
        self.database_url = os.getenv("DATABASE_URL", f"sqlite:///{self.database_path}")
        self.jwt_secret_key = os.getenv("JWT_SECRET_KEY", "cambia-esta-clave-en-produccion")
        self.jwt_algorithm = os.getenv("JWT_ALGORITHM", "HS256")
        self.access_token_expire_minutes = int(
            os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "120")
        )
        self.cors_origins = self._parse_cors_origins(os.getenv("CORS_ORIGINS"))

        self.data_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _parse_cors_origins(raw_value: str | None) -> list[str]:
        if not raw_value:
            return [
                "http://localhost:8000",
                "http://127.0.0.1:8000",
                "http://localhost:3000",
                "http://127.0.0.1:3000",
            ]
        return [origin.strip() for origin in raw_value.split(",") if origin.strip()]

    def require_elevenlabs(self) -> None:
        if not self.elevenlabs_api_key:
            raise RuntimeError("Falta ELEVENLABS_API_KEY en backend/.env")
        if not self.elevenlabs_agent_id:
            raise RuntimeError("Falta ELEVENLABS_AGENT_ID en backend/.env")

    def require_openai(self) -> None:
        if not self.openai_api_key:
            raise RuntimeError("Falta OPENAI_API_KEY en backend/.env")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
