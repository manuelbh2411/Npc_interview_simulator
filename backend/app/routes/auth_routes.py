from fastapi import APIRouter, Depends

from app.database import SessionLocal
from app.models.user import User
from app.schemas.auth_schema import TokenResponse, UserCreate, UserLogin, UserRead
from app.security.jwt import get_current_user
from app.services.auth_service import AuthService


router = APIRouter(prefix="/auth", tags=["Auth"])
auth_service = AuthService()


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(payload: UserCreate) -> TokenResponse:
    """Registra un usuario y devuelve un JWT listo para usar."""

    with SessionLocal() as db:
        return auth_service.register(db, payload)


@router.post("/login", response_model=TokenResponse)
async def login(payload: UserLogin) -> TokenResponse:
    """Valida email/contrasena y devuelve un JWT Bearer."""

    with SessionLocal() as db:
        return auth_service.login(db, payload)


@router.get("/me", response_model=UserRead)
async def me(current_user: User = Depends(get_current_user)) -> UserRead:
    """Devuelve los datos del usuario autenticado."""

    return UserRead.model_validate(current_user)
