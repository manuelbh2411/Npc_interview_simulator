# TFG - NPCs conversacionales para simulador de entrevistas

Titulo: **Aplicacion de LLMs para la mejora de personajes no jugadores (NPCs) en videojuegos**.

Este backend usa **ElevenLabs Conversational AI** para mantener la entrevista en tiempo real con el candidato. **OpenAI/GPT no entrevista al usuario**: solo analiza la transcripcion final y genera un informe estructurado de evaluacion.

## Arquitectura

```text
Unity / UI web local
  -> FastAPI
  -> ElevenLabs Conversational AI Agent mantiene la entrevista
  -> FastAPI guarda la transcripcion
  -> OpenAI evalua la entrevista terminada
  -> FastAPI devuelve informe JSON
```

## Estructura principal

```text
backend/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── models/
│   ├── services/
│   │   ├── elevenlabs_service.py
│   │   ├── transcript_service.py
│   │   ├── evaluation_service.py
│   │   └── interview_service.py
│   ├── prompts/
│   │   ├── interview_prompt.py
│   │   └── evaluation_prompt.py
│   ├── data/interviews/
│   └── static/
├── .env.example
├── requirements.txt
└── tests/
```

## Variables de entorno

Copia el ejemplo y rellena tus claves:

```bash
cd backend
cp .env.example .env
```

En `backend/.env`:

```env
ELEVENLABS_API_KEY=tu_clave_elevenlabs
ELEVENLABS_AGENT_ID=tu_agent_id
ELEVENLABS_VOICE_ID=tu_voice_id_opcional_no_es_el_agent_id
ELEVENLABS_BRANCH_ID=tu_branch_id_opcional
OPENAI_API_KEY=tu_clave_openai
OPENAI_EVALUATION_MODEL=gpt-4.1-mini
```

## Ejecutar en local

```bash
cd backend
source ../.venv/bin/activate
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Abre:

```text
http://127.0.0.1:8000/
```

Swagger:

```text
http://127.0.0.1:8000/docs
```

## Endpoints

- `GET /health`
- `GET /options`
- `GET /elevenlabs/signed-url`
- `POST /interview/start`
- `POST /interview/status`
- `POST /interview/stop`
- `POST /interview/transcript`
- `POST /interview/end`
- `GET /interview/{session_id}/report`

## Flujo para Unity

1. Unity llama a `POST /interview/start` con:

```json
{
  "job_type": "Ingeniería",
  "interviewer_personality": "Técnico",
  "candidate_name": "Manuel"
}
```

2. El backend pide a ElevenLabs una `signed_url` con `ELEVENLABS_API_KEY` y `ELEVENLABS_AGENT_ID`.

3. El backend devuelve `session_id`, `signed_url` y `conversation_overrides`. La API key nunca se expone al cliente.

4. Unity inicia la conversacion con ElevenLabs Conversational AI usando `signed_url` y los overrides.

5. Unity informa estados con `POST /interview/status`: `connecting`, `connected`, `stopping`, `stopped` o `error`.

6. Cada mensaje final transcrito se envia a `POST /interview/transcript`:

```json
{
  "session_id": "uuid",
  "speaker": "candidate",
  "message": "He trabajado en un proyecto de API REST.",
  "timestamp": "2026-05-11T19:30:00Z"
}
```

7. Al detener la llamada, Unity llama a `POST /interview/stop`. El backend solo permite detener si la sesion llego antes a `connected`.

8. Para generar el informe final, Unity llama a `POST /interview/end`.

9. OpenAI genera el informe final con puntuaciones, fortalezas, debilidades y recomendaciones.

## Pruebas

```bash
cd backend
../.venv/bin/python -m pytest
```
