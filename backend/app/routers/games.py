"""
API endpoints for games.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..database import get_db
from ..models import Game, Play
from ..schemas import GameResponse, GameListResponse, SeasonWeekResponse
from ..services import DataLoader

router = APIRouter(prefix="/api/games", tags=["games"])


@router.get("/seasons", response_model=SeasonWeekResponse)
def get_seasons(db: Session = Depends(get_db)):
    """Get available seasons and weeks from the database."""
    # Get distinct seasons
    seasons = (
        db.query(Game.season)
        .distinct()
        .order_by(Game.season.desc())
        .all()
    )
    seasons = [s[0] for s in seasons]

    # Get weeks for each season
    weeks_by_season = {}
    for season in seasons:
        weeks = (
            db.query(Game.week)
            .filter(Game.season == season)
            .distinct()
            .order_by(Game.week)
            .all()
        )
        weeks_by_season[season] = [w[0] for w in weeks]

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


@router.get("/top-momentum")
def get_top_momentum_games(
    category: str = Query("swings", description="Category: swings, comebacks, blowouts, close"),
    season: int = Query(None, description="Filter by season (omit for all)"),
    limit: int = Query(25, le=100),
    db: Session = Depends(get_db)
):
    """
    Get games with the most interesting momentum patterns.

    Categories:
    - swings: Games with biggest momentum swings
    - comebacks: Games where losing team came back (by momentum)
    - blowouts: Games with most one-sided momentum
    - close: Games with tight momentum throughout
    """
    from sqlalchemy import case, and_

    # Subquery to get momentum stats for each game
    momentum_stats = (
        db.query(
            Play.game_id,
            func.max(Play.home_momentum).label('max_home'),
            func.min(Play.home_momentum).label('min_home'),
            func.max(func.abs(Play.momentum_delta)).label('max_swing'),
            func.sum(func.abs(Play.momentum_delta)).label('total_volatility')
        )
        .group_by(Play.game_id)
        .subquery()
    )

    # Get final momentum for each game (last play)
    final_momentum = (
        db.query(
            Play.game_id,
            Play.home_momentum.label('final_home_momentum'),
            Play.away_momentum.label('final_away_momentum')
        )
        .distinct(Play.game_id)
        .order_by(Play.game_id, Play.play_id.desc())
        .subquery()
    )

    base_query = (
        db.query(
            Game,
            momentum_stats.c.max_home,
            momentum_stats.c.min_home,
            momentum_stats.c.max_swing,
            momentum_stats.c.total_volatility,
            final_momentum.c.final_home_momentum,
            final_momentum.c.final_away_momentum
        )
        .join(momentum_stats, Game.game_id == momentum_stats.c.game_id)
        .join(final_momentum, Game.game_id == final_momentum.c.game_id)
        .filter(Game.home_score.isnot(None))  # Only completed games
    )

    if season:
        base_query = base_query.filter(Game.season == season)

    if category == "swings":
        # Biggest single momentum swings
        results = base_query.order_by(momentum_stats.c.max_swing.desc()).limit(limit).all()
    elif category == "comebacks":
        # Games where team behind in momentum at halftime won the game
        # Use total volatility as proxy for comeback potential
        results = base_query.order_by(momentum_stats.c.total_volatility.desc()).limit(limit).all()
    elif category == "blowouts":
        # Most one-sided momentum (biggest difference between max and min home momentum)
        results = base_query.order_by(
            (momentum_stats.c.max_home - momentum_stats.c.min_home).desc()
        ).limit(limit).all()
    elif category == "close":
        # Games with smallest momentum range (competitive throughout)
        results = base_query.order_by(
            (momentum_stats.c.max_home - momentum_stats.c.min_home).asc()
        ).limit(limit).all()
    else:
        raise HTTPException(status_code=400, detail="Invalid category")

    return {
        "category": category,
        "games": [
            {
                **GameResponse.model_validate(r[0]).model_dump(),
                "max_home_momentum": r.max_home,
                "min_home_momentum": r.min_home,
                "max_swing": r.max_swing,
                "total_volatility": r.total_volatility,
                "final_home_momentum": r.final_home_momentum,
                "final_away_momentum": r.final_away_momentum
            }
            for r in results
        ],
        "count": len(results)
    }


@router.get("/stats/overview")
def get_stats_overview(
    season: int = Query(None, description="Filter by season (omit for all)"),
    db: Session = Depends(get_db)
):
    """Get overall statistics for momentum prediction accuracy."""
    from sqlalchemy import case

    # Get final momentum for each game
    final_momentum = (
        db.query(
            Play.game_id,
            Play.home_momentum.label('final_home_momentum'),
            Play.away_momentum.label('final_away_momentum')
        )
        .distinct(Play.game_id)
        .order_by(Play.game_id, Play.play_id.desc())
        .subquery()
    )

    query = (
        db.query(
            Game,
            final_momentum.c.final_home_momentum,
            final_momentum.c.final_away_momentum
        )
        .join(final_momentum, Game.game_id == final_momentum.c.game_id)
        .filter(Game.home_score.isnot(None))
    )

    if season:
        query = query.filter(Game.season == season)

    results = query.all()

    total_games = 0
    correct_predictions = 0
    home_wins = 0
    away_wins = 0
    momentum_favored_home = 0
    momentum_favored_away = 0

    for game, final_home, final_away in results:
        if game.home_score is None or game.away_score is None:
            continue
        if final_home is None or final_away is None:
            continue

        total_games += 1

        # Actual winner
        actual_home_win = game.home_score > game.away_score
        if actual_home_win:
            home_wins += 1
        else:
            away_wins += 1

        # Momentum prediction
        momentum_predicts_home = final_home > final_away
        if momentum_predicts_home:
            momentum_favored_home += 1
        else:
            momentum_favored_away += 1

        # Check if correct
        if momentum_predicts_home == actual_home_win:
            correct_predictions += 1

    accuracy = (correct_predictions / total_games * 100) if total_games > 0 else 0

    return {
        "total_games": total_games,
        "correct_predictions": correct_predictions,
        "accuracy_percentage": round(accuracy, 2),
        "home_wins": home_wins,
        "away_wins": away_wins,
        "momentum_favored_home": momentum_favored_home,
        "momentum_favored_away": momentum_favored_away,
        "season": season if season else "all"
    }


# Dynamic routes must come LAST to avoid catching specific routes
@router.get("/game/{game_id}", response_model=GameResponse)
def get_game(game_id: str, db: Session = Depends(get_db)):
    """Get a specific game by ID."""
    game = db.query(Game).filter(Game.game_id == game_id).first()

    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    return GameResponse.model_validate(game)


@router.post("/load/{season}")
def load_season(season: int, db: Session = Depends(get_db)):
    """Load a season's data from nfl_data_py."""
    loader = DataLoader(db)
    result = loader.load_season(season)
    return result


@router.get("/{season}/{week}", response_model=GameListResponse)
def get_games_by_week(
    season: int,
    week: int,
    db: Session = Depends(get_db)
):
    """Get all games for a specific season and week."""
    games = (
        db.query(Game)
        .filter(Game.season == season, Game.week == week)
        .order_by(Game.game_date)
        .all()
    )

    return GameListResponse(
        games=[GameResponse.model_validate(g) for g in games],
        count=len(games)
    )
