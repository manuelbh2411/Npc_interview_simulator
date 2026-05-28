from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.interview import Interview
from app.models.user import User
from app.schemas.game_schema import AchievementRead, AvatarIconRead, PlayerStatsResponse, RankingEntry


PERSONALITY_XP_BONUS = {
    "Amable": 80,
    "RRHH": 100,
    "Startup informal": 115,
    "Técnico": 135,
    "Agresivo": 155,
}

AVATAR_UNLOCKS = [
    ("target", "Aspirante enfocado", "🎯", 1),
    ("diamond", "Candidato brillante", "💎", 3),
    ("spark", "Respuesta rapida", "⚡", 6),
    ("shield", "Perfil solido", "🛡", 9),
    ("trophy", "Profesional destacado", "🏆", 12),
    ("crown", "Maestro de entrevistas", "👑", 15),
]


@dataclass(frozen=True)
class _Progress:
    total_xp: int
    level: int
    rank: str
    current_level_xp: int
    next_level_xp: int
    progress_percent: int


class GameProgressService:
    """Calcula la capa de serious game a partir de entrevistas reales."""

    def _xp_for_score(self, score: float | None, personality: str | None = None) -> int:
        if score is None:
            return 0
        return int(round(score * 100)) + PERSONALITY_XP_BONUS.get(personality or "", 75)

    def _level_floor(self, level: int) -> int:
        return 350 * (level - 1) * level // 2

    def _progress(self, total_xp: int) -> _Progress:
        level = 1
        while total_xp >= self._level_floor(level + 1):
            level += 1

        current_floor = self._level_floor(level)
        next_floor = self._level_floor(level + 1)
        current_level_xp = max(0, total_xp - current_floor)
        next_level_xp = max(1, next_floor - current_floor)
        progress_percent = min(100, int((current_level_xp / next_level_xp) * 100))

        if level <= 3:
            rank = "Aspirante"
        elif level <= 6:
            rank = "Candidato en progreso"
        elif level <= 10:
            rank = "Profesional preparado"
        else:
            rank = "Experto en entrevistas"

        return _Progress(
            total_xp=total_xp,
            level=level,
            rank=rank,
            current_level_xp=current_level_xp,
            next_level_xp=next_level_xp,
            progress_percent=progress_percent,
        )

    def _interviews(self, db: Session, user_id: int) -> list[Interview]:
        return list(
            db.scalars(
                select(Interview)
                .where(Interview.user_id == user_id)
                .order_by(Interview.created_at.desc())
            ).all()
        )

    def _score_values(self, interviews: list[Interview]) -> list[float]:
        return [
            interview.report.overall_score
            for interview in interviews
            if interview.report and interview.report.overall_score is not None
        ]

    def _achievements(
        self,
        interviews: list[Interview],
        scores: list[float],
    ) -> list[AchievementRead]:
        completed = [item for item in interviews if item.status == "completed"]
        technical_completed = [
            item for item in completed if item.job_type in {"Ingeniería"} and item.report
        ]
        communication_high = any(
            item.report and item.report.communication_score >= 8 for item in completed
        )
        improved = len(scores) >= 2 and scores[0] > scores[-1]

        definitions = [
            (
                "first_clear",
                "Primera entrevista completada",
                "Has terminado tu primera simulacion con informe.",
                len(completed) >= 1,
            ),
            (
                "five_runs",
                "Rutina de entrenamiento",
                "Has completado 5 entrevistas.",
                len(completed) >= 5,
            ),
            (
                "score_eight",
                "Candidato prometedor",
                "Has superado una puntuacion final de 8.",
                any(score >= 8 for score in scores),
            ),
            (
                "tech_specialist",
                "Especialista tecnico",
                "Has completado una entrevista de Ingenieria con informe.",
                len(technical_completed) >= 1,
            ),
            (
                "communication",
                "Comunicacion excelente",
                "Has logrado 8 o mas en comunicacion.",
                communication_high,
            ),
            (
                "improvement",
                "Mejora notable",
                "Tu ultima puntuacion supera una anterior.",
                improved,
            ),
        ]
        return [
            AchievementRead(
                code=code,
                title=title,
                description=description,
                unlocked=unlocked,
            )
            for code, title, description, unlocked in definitions
        ]

    def _avatar_icons(self, level: int) -> list[AvatarIconRead]:
        return [
            AvatarIconRead(
                code=code,
                title=title,
                symbol=symbol,
                required_level=required_level,
                unlocked=level >= required_level,
            )
            for code, title, symbol, required_level in AVATAR_UNLOCKS
        ]

    def player_stats(self, db: Session, user: User) -> PlayerStatsResponse:
        interviews = self._interviews(db, user.id)
        scores = self._score_values(interviews)
        total_xp = sum(
            self._xp_for_score(interview.report.overall_score, interview.personality)
            for interview in interviews
            if interview.report and interview.report.overall_score is not None
        )
        progress = self._progress(total_xp)
        total_duration = sum(item.duration_seconds or 0 for item in interviews)

        return PlayerStatsResponse(
            user_id=user.id,
            name=user.name,
            total_xp=progress.total_xp,
            level=progress.level,
            rank=progress.rank,
            current_level_xp=progress.current_level_xp,
            next_level_xp=progress.next_level_xp,
            progress_percent=progress.progress_percent,
            completed_interviews=len([item for item in interviews if item.status == "completed"]),
            total_interviews=len(interviews),
            average_score=round(sum(scores) / len(scores), 1) if scores else None,
            best_score=max(scores) if scores else None,
            total_duration_seconds=total_duration,
            achievements=self._achievements(interviews, scores),
            avatar_icons=self._avatar_icons(progress.level),
        )

    def _is_public_ranking_user(self, user: User) -> bool:
        email = user.email.lower()
        name = user.name.strip().lower()
        synthetic_email = email.endswith("@example.com")
        synthetic_name = name in {"test", "test01", "test1", "prueba"}
        return not synthetic_email and not synthetic_name

    def ranking(self, db: Session, limit: int = 10) -> list[RankingEntry]:
        users = [
            user
            for user in db.scalars(select(User)).all()
            if self._is_public_ranking_user(user)
        ]
        entries: list[RankingEntry] = []
        for user in users:
            stats = self.player_stats(db, user)
            entries.append(
                RankingEntry(
                    position=0,
                    user_id=user.id,
                    name=user.name,
                    total_xp=stats.total_xp,
                    level=stats.level,
                    rank=stats.rank,
                    average_score=stats.average_score,
                    completed_interviews=stats.completed_interviews,
                )
            )

        entries.sort(key=lambda item: (item.total_xp, item.average_score or 0), reverse=True)
        return [
            RankingEntry(**{**entry.model_dump(), "position": index + 1})
            for index, entry in enumerate(entries[:limit])
        ]
