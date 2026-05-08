"""
API endpoints for games.
"""
from fastapi import APIRouter, Depends, HTTPException, Header, Query, Response
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..config import get_settings
from ..database import get_db
from ..models import Game, Play
from ..schemas import GameResponse, GameListResponse, SeasonWeekResponse
from ..services import DataLoader

settings = get_settings()

router = APIRouter(prefix="/api/games", tags=["games"])


@router.get("/seasons", response_model=SeasonWeekResponse)
def get_seasons(db: Session = Depends(get_db)):
    """Get available seasons and weeks from the database."""
    results = (
        db.query(Game.season, Game.week)
        .distinct()
        .order_by(Game.season.desc(), Game.week)
        .all()
    )
    weeks_by_season: dict[int, list[int]] = {}
    for season, week in results:
        weeks_by_season.setdefault(season, []).append(week)
    seasons = sorted(weeks_by_season.keys(), reverse=True)

    return SeasonWeekResponse(seasons=seasons, weeks_by_season=weeks_by_season)


@router.get("/available-seasons")
def get_available_seasons_to_load(db: Session = Depends(get_db)):
    """Get seasons available to load from nfl_data_py."""
    loader = DataLoader(db)
    all_seasons = loader.get_available_seasons()

    # Get already loaded seasons
    loaded = (
        db.query(Game.season)
        .distinct()
        .all()
    )
    loaded_seasons = {s[0] for s in loaded}

    return {
        "all_seasons": all_seasons,
        "loaded_seasons": list(loaded_seasons),
        "available_to_load": [s for s in all_seasons if s not in loaded_seasons]
    }


@router.get("/search")
def search_games(
    q: str = Query(..., min_length=2, description="Search query (team name)"),
    season: int = Query(None, description="Filter by season"),
    limit: int = Query(20, le=100),
    db: Session = Depends(get_db)
):
    """Search for games by team name."""
    query = db.query(Game).filter(
        (Game.home_team.ilike(f"%{q}%")) | (Game.away_team.ilike(f"%{q}%"))
    )

    if season:
        query = query.filter(Game.season == season)

    games = query.order_by(Game.season.desc(), Game.week.desc()).limit(limit).all()

    return GameListResponse(
        games=[GameResponse.model_validate(g) for g in games],
        count=len(games)
    )


# Dynamic routes must come LAST to avoid catching specific routes
@router.get("/game/{game_id}", response_model=GameResponse)
def get_game(game_id: str, db: Session = Depends(get_db), response: Response = None):
    """Get a specific game by ID."""
    game = db.query(Game).filter(Game.game_id == game_id).first()

    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    if response and game.home_score is not None:
        response.headers["Cache-Control"] = "public, max-age=3600"

    return GameResponse.model_validate(game)


@router.post("/load/{season}")
def load_season(
    season: int,
    db: Session = Depends(get_db),
    x_admin_key: str = Header(None)
):
    """Load a season's data from nfl_data_py."""
    if settings.admin_key and x_admin_key != settings.admin_key:
        raise HTTPException(status_code=403, detail="Forbidden")
    loader = DataLoader(db)
    result = loader.load_season(season)
    return result


@router.get("/{season}/{week}", response_model=GameListResponse)
def get_games_by_week(
    season: int,
    week: int,
    db: Session = Depends(get_db),
    response: Response = None
):
    """Get all games for a specific season and week."""
    games = (
        db.query(Game)
        .filter(Game.season == season, Game.week == week)
        .order_by(Game.game_date)
        .all()
    )

    if response:
        response.headers["Cache-Control"] = "public, max-age=3600"

    return GameListResponse(
        games=[GameResponse.model_validate(g) for g in games],
        count=len(games)
    )
