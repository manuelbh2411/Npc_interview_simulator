from uuid import uuid4

from app.main import app
from app.models.evaluation_models import EvaluationReport
from app.models.interview_models import ElevenLabsSessionData
from app.routes.interview_routes import interview_service as user_interview_service
from tests.asgi_test_client import request


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _register_user(email: str) -> str:
    response = request(
        app,
        "POST",
        "/auth/register",
        {
            "name": "Manuel",
            "email": email,
            "password": "password-segura-123",
        },
    )
    assert response.status_code == 201
    return response.json()["access_token"]


def test_register_login_and_me() -> None:
    email = f"manuel-{uuid4()}@example.com"
    token = _register_user(email)

    me = request(app, "GET", "/auth/me", headers=_auth_headers(token))

    assert me.status_code == 200
    assert me.json()["email"] == email

    login = request(
        app,
        "POST",
        "/auth/login",
        {"email": email, "password": "password-segura-123"},
    )

    assert login.status_code == 200
    assert login.json()["token_type"] == "bearer"


def test_authenticated_interview_history_report_and_delete(monkeypatch) -> None:
    def fake_start_conversation(*args, **kwargs):
        return (
            ElevenLabsSessionData(
                signed_url="wss://example.test/signed",
                agent_id="test-agent",
                conversation_overrides={"agent": {"firstMessage": "Hola, soy Carolina."}},
            ),
            "Hola, soy Carolina.",
        )

    def fake_evaluate_interview(interview):
        return EvaluationReport(
            overall_score=8.2,
            communication_score=8,
            coherence_score=8.5,
            job_fit_score=8,
            confidence_score=7.5,
            strengths=["Respuesta clara."],
            weaknesses=["Puede aportar mas metricas."],
            recommendations=["Preparar ejemplos STAR."],
            summary_report="Buena entrevista tecnica.",
            final_feedback="Perfil prometedor.",
        )

    monkeypatch.setattr(
        user_interview_service.elevenlabs,
        "start_conversation",
        fake_start_conversation,
    )
    monkeypatch.setattr(
        user_interview_service.evaluator,
        "evaluate_interview",
        fake_evaluate_interview,
    )

    token = _register_user(f"historial-{uuid4()}@example.com")
    headers = _auth_headers(token)

    start = request(
        app,
        "POST",
        "/interviews/start",
        {
            "title": "Software Engineering Interview",
            "job_type": "Ingeniería",
            "interviewer_personality": "Técnico",
        },
        headers=headers,
    )

    assert start.status_code == 200
    interview_id = start.json()["id"]

    message = request(
        app,
        "POST",
        f"/interviews/{interview_id}/message",
        {
            "speaker": "candidate",
            "message": "He trabajado en APIs con Python y FastAPI.",
        },
        headers=headers,
    )

    assert message.status_code == 200
    assert message.json()["message_count"] == 1

    end = request(app, "POST", f"/interviews/{interview_id}/end", headers=headers)

    assert end.status_code == 200
    assert end.json()["report"]["overall_score"] == 8.2

    history = request(app, "GET", "/interviews", headers=headers)

    assert history.status_code == 200
    assert history.json()[0]["title"] == "Software Engineering Interview"
    assert history.json()[0]["has_report"] is True

    report = request(app, "GET", f"/interviews/{interview_id}/report", headers=headers)

    assert report.status_code == 200
    assert report.json()["final_feedback"] == "Perfil prometedor."

    deleted = request(app, "DELETE", f"/interviews/{interview_id}", headers=headers)

    assert deleted.status_code == 200
    assert deleted.json()["deleted"] is True
