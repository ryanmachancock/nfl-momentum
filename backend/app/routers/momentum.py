"""
API endpoints for momentum calculation.
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Game
from ..schemas import GameResponse, MomentumResponse, MomentumDataPoint
from ..services import MomentumCalculator, GraphExporter

router = APIRouter(prefix="/api/momentum", tags=["momentum"])


@router.get("/{game_id}", response_model=MomentumResponse)
def get_momentum(game_id: str, db: Session = Depends(get_db)):
    """Get momentum data for a game."""
    game = db.query(Game).filter(Game.game_id == game_id).first()

    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    calculator = MomentumCalculator(db)
    data_points = calculator.calculate_game_momentum(game_id)
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


@router.post("/{game_id}/refresh")
def refresh_momentum(game_id: str, db: Session = Depends(get_db)):
    """Recalculate momentum for a game."""
    game = db.query(Game).filter(Game.game_id == game_id).first()

    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    calculator = MomentumCalculator(db)
    data_points = calculator.calculate_game_momentum(game_id)

    return {
        "message": "Momentum recalculated",
        "game_id": game_id,
        "play_count": len(data_points)
    }


@router.get("/{game_id}/export/png")
def export_png(game_id: str, db: Session = Depends(get_db)):
    """Export momentum graph as PNG."""
    game = db.query(Game).filter(Game.game_id == game_id).first()

    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    calculator = MomentumCalculator(db)
    data_points = calculator.calculate_game_momentum(game_id)
    normalized = calculator.get_normalized_momentum(data_points)

    exporter = GraphExporter()
    png_bytes = exporter.generate_png(
        GameResponse.model_validate(game),
        normalized
    )

    filename = f"momentum_{game.away_team}_at_{game.home_team}_week{game.week}_{game.season}.png"

    return Response(
        content=png_bytes,
        media_type="image/png",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/{game_id}/export/svg")
def export_svg(game_id: str, db: Session = Depends(get_db)):
    """Export momentum graph as SVG."""
    game = db.query(Game).filter(Game.game_id == game_id).first()

    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    calculator = MomentumCalculator(db)
    data_points = calculator.calculate_game_momentum(game_id)
    normalized = calculator.get_normalized_momentum(data_points)

    exporter = GraphExporter()
    svg_content = exporter.generate_svg(
        GameResponse.model_validate(game),
        normalized
    )

    filename = f"momentum_{game.away_team}_at_{game.home_team}_week{game.week}_{game.season}.svg"

    return Response(
        content=svg_content,
        media_type="image/svg+xml",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
