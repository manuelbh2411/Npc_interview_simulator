from app.main import app
from tests.asgi_test_client import request


def test_root_serves_interview_ui() -> None:
    response = request(app, "GET", "/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Crear cuenta" in response.text
    assert "Iniciar sesion" in response.text


def test_setup_route_serves_interview_selector() -> None:
    response = request(app, "GET", "/setup")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Selecciona tu entrevistador" in response.text


def test_dashboard_route_serves_user_history() -> None:
    response = request(app, "GET", "/dashboard")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Historial de entrevistas" in response.text
    assert "Nueva entrevista" in response.text


def test_interview_route_serves_room_ui() -> None:
    response = request(app, "GET", "/interview")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Sala de reunion virtual" in response.text


def test_realtime_route_serves_room_ui() -> None:
    response = request(app, "GET", "/realtime")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Sala de reunion virtual" in response.text
    assert "Hablar con microfono" not in response.text
    assert "Parar voz" not in response.text
    assert "Detener entrevista" in response.text
    assert "Iniciar entrevista" in response.text
