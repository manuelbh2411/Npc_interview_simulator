from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.auth_schema import TokenResponse, UserCreate, UserLogin, UserRead
from app.security.jwt import create_access_token
from app.security.password import hash_password, verify_password


class AuthService:
    """Casos de uso de registro, login y lectura del usuario actual."""

    def get_by_email(self, db: Session, email: str) -> User | None:
        return db.scalar(select(User).where(User.email == email.lower()))

    def register(self, db: Session, payload: UserCreate) -> TokenResponse:
        if self.get_by_email(db, payload.email):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ya existe un usuario registrado con ese email",
            )

        user = User(
            name=payload.name.strip(),
            email=payload.email,
            hashed_password=hash_password(payload.password),
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        token = create_access_token(user.id, {"email": user.email})
        return TokenResponse(access_token=token, user=UserRead.model_validate(user))

    def login(self, db: Session, payload: UserLogin) -> TokenResponse:
        user = self.get_by_email(db, payload.email)
        if not user or not verify_password(payload.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email o contrasena incorrectos",
                headers={"WWW-Authenticate": "Bearer"},
            )

        token = create_access_token(user.id, {"email": user.email})
        return TokenResponse(access_token=token, user=UserRead.model_validate(user))
