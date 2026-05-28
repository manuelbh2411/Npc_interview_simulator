from pathlib import Path
import sys


BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from app.config import settings  # noqa: E402
from app.database import init_db  # noqa: E402


if __name__ == "__main__":
    init_db()
    print(f"Base de datos preparada en: {settings.database_url}")
