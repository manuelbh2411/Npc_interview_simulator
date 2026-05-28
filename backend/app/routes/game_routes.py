from fastapi import APIRouter, Depends

from app.database import SessionLocal
from app.models.user import User
from app.schemas.game_schema import PlayerStatsResponse, RankingEntry
from app.security.jwt import get_current_user
from app.services.game_progress_service import GameProgressService


router = APIRouter(prefix="/game", tags=["Game Progress"])
game_service = GameProgressService()


@router.get("/profile", response_model=PlayerStatsResponse)
async def player_profile(current_user: User = Depends(get_current_user)) -> PlayerStatsResponse:
    """Devuelve nivel, XP, rango, logros y estadisticas del jugador."""

    with SessionLocal() as db:
        return game_service.player_stats(db, current_user)


@router.get("/ranking", response_model=list[RankingEntry])
async def ranking(current_user: User = Depends(get_current_user)) -> list[RankingEntry]:
    """Ranking local de usuarios por XP acumulada."""

    with SessionLocal() as db:
        return game_service.ranking(db)

