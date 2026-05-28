from app.main import app
from tests.asgi_test_client import request


def test_health_returns_ok() -> None:
    response = request(app, "GET", "/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_options_returns_jobs_and_personalities() -> None:
    response = request(app, "GET", "/options")

    assert response.status_code == 200
    data = response.json()
    assert "Ingeniería" in data["jobs"]
    assert "Marketing" in data["jobs"]
    assert "Amable" in data["personalities"]
    assert "Startup informal" in data["personalities"]
