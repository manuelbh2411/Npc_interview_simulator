from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from app.config import settings
from app.database import SessionLocal
from app.models.user import User


bearer_scheme = HTTPBearer()


def create_access_token(subject: str | int, extra_data: dict[str, Any] | None = None) -> str:
    """Crea un JWT con expiracion para autenticar llamadas desde Unity/frontend."""

    expire = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)
    payload: dict[str, Any] = {
        "sub": str(subject),
        "exp": expire,
    }
    if extra_data:
        payload.update(extra_data)
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token no valido o expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )
    token = credentials.credentials
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError as exc:
        raise credentials_exception from exc

    try:
        user_id_int = int(user_id)
    except (TypeError, ValueError) as exc:
        raise credentials_exception from exc

    with SessionLocal() as db:
        user = db.get(User, user_id_int)
        if user is None:
            raise credentials_exception
        return user
