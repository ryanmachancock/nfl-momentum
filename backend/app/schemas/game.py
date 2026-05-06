from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional


class GameBase(BaseModel):
    game_id: str
    season: int
    week: int
    game_type: Optional[str] = None
    home_team: str
    away_team: str
    home_score: Optional[int] = None
    away_score: Optional[int] = None
    game_date: Optional[date] = None


class GameCreate(GameBase):
    pass


class GameResponse(GameBase):
    id: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class GameListResponse(BaseModel):
    games: list[GameResponse]
    count: int


class PlayResponse(BaseModel):
    play_id: int
    quarter: Optional[int] = None
    time_remaining: Optional[str] = None
    down: Optional[int] = None
    yards_to_go: Optional[int] = None
    yard_line: Optional[int] = None
    posteam: Optional[str] = None
    defteam: Optional[str] = None
    play_type: Optional[str] = None
    yards_gained: Optional[int] = None
    description: Optional[str] = None

    # Key events for display
    touchdown: bool = False
    interception: bool = False
    fumble_lost: bool = False
    sack: bool = False
    safety: bool = False

    # Momentum
    home_momentum: float = 0.0
    away_momentum: float = 0.0
    momentum_delta: float = 0.0

    class Config:
        from_attributes = True


class MomentumDataPoint(BaseModel):
    play_id: int
    quarter: int
    time_remaining: str
    home_momentum: float
    away_momentum: float
    momentum_delta: float
    home_wp: Optional[float] = None  # Win probability (0-1)
    away_wp: Optional[float] = None
    # Score tracking
    home_score: int = 0
    away_score: int = 0
    # Context for leverage calculation
    yardline_100: Optional[int] = None  # Yards from opponent's end zone
    down: Optional[int] = None
    yards_to_go: Optional[int] = None
    event_description: Optional[str] = None
    is_significant: bool = False  # For highlighting big momentum swings


class MomentumResponse(BaseModel):
    game: GameResponse
    data_points: list[MomentumDataPoint]
    max_momentum: float
    min_momentum: float
    biggest_swing: Optional[MomentumDataPoint] = None


class ShareResponse(BaseModel):
    share_code: str
    share_url: str
    game_id: str


class SeasonWeekResponse(BaseModel):
    seasons: list[int]
    weeks_by_season: dict[int, list[int]]
