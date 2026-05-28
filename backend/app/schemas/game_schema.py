from pydantic import BaseModel


class AchievementRead(BaseModel):
    code: str
    title: str
    description: str
    unlocked: bool


class AvatarIconRead(BaseModel):
    code: str
    title: str
    symbol: str
    required_level: int
    unlocked: bool


class PlayerStatsResponse(BaseModel):
    user_id: int
    name: str
    total_xp: int
    level: int
    rank: str
    current_level_xp: int
    next_level_xp: int
    progress_percent: int
    completed_interviews: int
    total_interviews: int
    average_score: float | None
    best_score: float | None
    total_duration_seconds: int
    achievements: list[AchievementRead]
    avatar_icons: list[AvatarIconRead]


class RankingEntry(BaseModel):
    position: int
    user_id: int
    name: str
    total_xp: int
    level: int
    rank: str
    average_score: float | None
    completed_interviews: int
