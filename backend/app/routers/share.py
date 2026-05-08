"""
API endpoints for sharing momentum graphs.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from nanoid import generate

from ..config import get_settings
from ..database import get_db
from ..models import Game, SharedGraph
from ..schemas import GameResponse, MomentumResponse, ShareResponse
from ..services import MomentumCalculator

settings = get_settings()

router = APIRouter(prefix="/api/share", tags=["share"])


def generate_share_code() -> str:
    """Generate a unique share code."""
    # Use nanoid for URL-safe, short codes
    return generate(size=10)


@router.post("/{game_id}", response_model=ShareResponse)
def create_share_link(
    game_id: str,
    db: Session = Depends(get_db)
):
    """Create a shareable link for a game's momentum graph."""
    game = db.query(Game).filter(Game.game_id == game_id).first()

    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    # Check if share already exists for this game
    existing = db.query(SharedGraph).filter(SharedGraph.game_id == game_id).first()

    if existing:
        share_code = existing.share_code
    else:
        # Create new share
        share_code = generate_share_code()
        shared = SharedGraph(
            share_code=share_code,
            game_id=game_id
        )
        db.add(shared)
        db.commit()

    share_url = f"{settings.frontend_url}/s/{share_code}"

    return ShareResponse(
        share_code=share_code,
        share_url=share_url,
        game_id=game_id
    )


@router.get("/{share_code}", response_model=MomentumResponse)
def get_shared_graph(share_code: str, db: Session = Depends(get_db)):
    """Get momentum data for a shared graph."""
    shared = db.query(SharedGraph).filter(SharedGraph.share_code == share_code).first()

    if not shared:
        raise HTTPException(status_code=404, detail="Share link not found")

    # Increment view count
    shared.view_count += 1
    db.commit()

    game = shared.game

    calculator = MomentumCalculator(db)
    data_points = calculator.calculate_game_momentum(game.game_id)
    normalized = calculator.get_normalized_momentum(data_points)

    # Find biggest swing
    biggest_swing = None
    max_swing = 0
    for dp in normalized:
        if abs(dp.momentum_delta) > max_swing:
            max_swing = abs(dp.momentum_delta)
            biggest_swing = dp

    # Get max/min
    if normalized:
        max_momentum = max(dp.home_momentum for dp in normalized)
        min_momentum = min(dp.home_momentum for dp in normalized)
    else:
        max_momentum = 0
        min_momentum = 0

    return MomentumResponse(
        game=GameResponse.model_validate(game),
        data_points=normalized,
        max_momentum=max_momentum,
        min_momentum=min_momentum,
        biggest_swing=biggest_swing
    )


@router.get("/{share_code}/stats")
def get_share_stats(share_code: str, db: Session = Depends(get_db)):
    """Get stats for a shared link."""
    shared = db.query(SharedGraph).filter(SharedGraph.share_code == share_code).first()

    if not shared:
        raise HTTPException(status_code=404, detail="Share link not found")

    return {
        "share_code": shared.share_code,
        "game_id": shared.game_id,
        "created_at": shared.created_at,
        "view_count": shared.view_count
    }
