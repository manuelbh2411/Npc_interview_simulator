import asyncio
import json
from dataclasses import dataclass
from typing import Any


@dataclass
class ASGIResponse:
    status_code: int
    headers: dict[str, str]
    body: bytes

    @property
    def text(self) -> str:
        return self.body.decode("utf-8")

    def json(self) -> Any:
        return json.loads(self.text)


def request(
    app: Any,
    method: str,
    path: str,
    json_body: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> ASGIResponse:
    return asyncio.run(_request(app, method, path, json_body, headers))


async def _request(
    app: Any,
    method: str,
    path: str,
    json_body: dict[str, Any] | None,
    extra_headers: dict[str, str] | None,
) -> ASGIResponse:
    body = b""
    headers: list[tuple[bytes, bytes]] = []
    if json_body is not None:
        body = json.dumps(json_body).encode("utf-8")
        headers.append((b"content-type", b"application/json"))
    if extra_headers:
        for key, value in extra_headers.items():
            headers.append((key.lower().encode("latin-1"), value.encode("latin-1")))

    sent_request = False
    messages: list[dict[str, Any]] = []

    async def receive() -> dict[str, Any]:
        nonlocal sent_request
        if not sent_request:
            sent_request = True
            return {"type": "http.request", "body": body, "more_body": False}
        await asyncio.sleep(3600)
        return {"type": "http.disconnect"}

    async def send(message: dict[str, Any]) -> None:
        messages.append(message)

    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": method,
        "scheme": "http",
        "path": path,
        "raw_path": path.encode("ascii"),
        "query_string": b"",
        "headers": headers,
        "client": ("testclient", 50000),
        "server": ("testserver", 80),
    }

    await app(scope, receive, send)

    status = 500
    response_headers: dict[str, str] = {}
    chunks: list[bytes] = []
    for message in messages:
        if message["type"] == "http.response.start":
            status = message["status"]
            response_headers = {
                key.decode("latin-1").lower(): value.decode("latin-1")
                for key, value in message.get("headers", [])
            }
        elif message["type"] == "http.response.body":
            chunks.append(message.get("body", b""))

    return ASGIResponse(status_code=status, headers=response_headers, body=b"".join(chunks))
