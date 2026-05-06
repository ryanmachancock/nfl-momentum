"""
API endpoints for statistics and validation metrics.
Updated with multiple prediction methods comparison.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from typing import List, Dict, Any

from ..database import get_db
from ..models import Game, Play
from ..schemas import GameResponse
from ..services import MomentumCalculator

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("/overview")
def get_stats_overview(
    season: int = None,
    db: Session = Depends(get_db)
):
    """Get overall statistics for momentum prediction accuracy across all or one season.
    Uses pre-calculated momentum values from the database for fast queries."""

    # Get max momentum per game (as proxy for final momentum - much faster query)
    momentum_stats = (
        db.query(
            Play.game_id,
            func.max(Play.home_momentum).label('max_home'),
            func.max(Play.away_momentum).label('max_away')
        )
        .filter(Play.home_momentum.isnot(None))
        .group_by(Play.game_id)
        .subquery()
    )

    # Join with games to get scores
    base_query = (
        db.query(
            Game.game_id,
            Game.home_score,
            Game.away_score,
            momentum_stats.c.max_home,
            momentum_stats.c.max_away
        )
        .join(momentum_stats, Game.game_id == momentum_stats.c.game_id)
        .filter(Game.home_score.isnot(None))
        .filter(Game.away_score.isnot(None))
        .filter(Game.home_score != Game.away_score)  # Exclude ties
    )

    if season:
        base_query = base_query.filter(Game.season == season)

    results = base_query.all()

    total_games = 0
    correct_predictions = 0
    home_wins = 0
    away_wins = 0
    momentum_favored_home = 0
    momentum_favored_away = 0

    for row in results:
        game_id, home_score, away_score, max_home, max_away = row
        max_home = max_home or 0
        max_away = max_away or 0

        total_games += 1

        # Actual winner
        actual_home_win = home_score > away_score
        if actual_home_win:
            home_wins += 1
        else:
            away_wins += 1

        # Momentum prediction (using max momentum as proxy)
        momentum_predicts_home = max_home > max_away
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


@router.get("/top-momentum")
def get_top_momentum_games(
    category: str = "swings",
    season: int = None,
    limit: int = 25,
    db: Session = Depends(get_db)
):
    """
    Get games with the most interesting momentum patterns.
    Uses pre-calculated momentum values from the database for fast queries.

    Categories:
    - swings: Games with biggest momentum swings
    - comebacks: Games with most total volatility
    - blowouts: Games with most one-sided momentum
    - close: Games with tight momentum throughout
    """
    # Use database aggregation for fast stats calculation
    # Query momentum stats directly from plays table with a single efficient query
    momentum_stats = (
        db.query(
            Play.game_id,
            func.max(Play.home_momentum).label('max_home'),
            func.min(Play.home_momentum).label('min_home'),
            func.max(func.abs(Play.momentum_delta)).label('max_swing'),
            func.sum(func.abs(Play.momentum_delta)).label('total_volatility'),
            func.max(Play.away_momentum).label('max_away')
        )
        .filter(Play.home_momentum.isnot(None))
        .group_by(Play.game_id)
        .subquery()
    )

    # Build main query joining games with stats
    base_query = (
        db.query(
            Game,
            momentum_stats.c.max_home,
            momentum_stats.c.min_home,
            momentum_stats.c.max_swing,
            momentum_stats.c.total_volatility,
            momentum_stats.c.max_away
        )
        .join(momentum_stats, Game.game_id == momentum_stats.c.game_id)
        .filter(Game.home_score.isnot(None))
    )

    if season:
        base_query = base_query.filter(Game.season == season)

    # Calculate momentum range for sorting (max_home - min_home)
    momentum_range = momentum_stats.c.max_home - momentum_stats.c.min_home

    # Sort based on category using SQL ORDER BY
    if category == "swings":
        base_query = base_query.order_by(momentum_stats.c.max_swing.desc())
    elif category == "comebacks":
        base_query = base_query.order_by(momentum_stats.c.total_volatility.desc())
    elif category == "blowouts":
        base_query = base_query.order_by(momentum_range.desc())
    elif category == "close":
        base_query = base_query.order_by(momentum_range.asc())
    else:
        base_query = base_query.order_by(momentum_stats.c.max_swing.desc())

    # Apply limit and execute query
    results = base_query.limit(limit).all()

    # Format results
    games_list = []
    for row in results:
        game = row[0]  # Game object
        max_home = row[1] or 0
        min_home = row[2] or 0
        max_swing = row[3] or 0
        total_volatility = row[4] or 0
        max_away = row[5] or 0

        games_list.append({
            **GameResponse.model_validate(game).model_dump(),
            "max_home_momentum": round(float(max_home), 2),
            "min_home_momentum": round(float(min_home), 2),
            "max_swing": round(float(max_swing), 2),
            "total_volatility": round(float(total_volatility), 2),
            # Use max values as approximations for final momentum (avoids slow query)
            "final_home_momentum": round(float(max_home), 2),
            "final_away_momentum": round(float(max_away), 2)
        })

    return {
        "category": category,
        "games": games_list,
        "count": len(games_list)
    }


@router.get("/season/{season}")
def get_season_stats(season: int, db: Session = Depends(get_db)):
    """
    Get season summary statistics including multiple validation metrics.

    Returns:
        - Total games
        - Multiple validation metrics comparing different prediction methods
        - Games ranked by biggest momentum swing
        - Average momentum swings per game
    """
    # Get all games for the season (exclude ties)
    games = (
        db.query(Game)
        .filter(Game.season == season)
        .filter(Game.home_score.isnot(None))
        .filter(Game.away_score.isnot(None))
        .filter(Game.home_score != Game.away_score)  # Exclude ties
        .all()
    )

    if not games:
        raise HTTPException(status_code=404, detail=f"No games found for season {season}")

    calculator = MomentumCalculator(db)

    # Analyze each game
    game_analyses = []
    total_analyzed = 0

    # Track predictions for each metric
    metrics = {
        "final_momentum": {"correct": 0, "description": "Team with momentum at game end"},
        "total_generated": {"correct": 0, "description": "Team that generated more total positive momentum"},
        "lead_duration": {"correct": 0, "description": "Team that held momentum lead for more plays"},
        "peak_momentum": {"correct": 0, "description": "Team that achieved highest momentum peak"},
        "average_momentum": {"correct": 0, "description": "Team with higher average momentum throughout"},
    }

    for game in games:
        try:
            # Calculate momentum for this game
            data_points = calculator.calculate_game_momentum(game.game_id)

            if not data_points:
                continue

            # Determine actual winner
            actual_home_won = game.home_score > game.away_score

            # ===== METRIC 1: Final Momentum (current) =====
            final_play = data_points[-1]
            final_home_momentum = final_play.home_momentum
            final_predicts_home = final_home_momentum > 0

            # ===== METRIC 2: Total Generated Momentum =====
            # Sum of all positive deltas for each team
            home_total_generated = sum(dp.momentum_delta for dp in data_points if dp.momentum_delta > 0)
            away_total_generated = sum(abs(dp.momentum_delta) for dp in data_points if dp.momentum_delta < 0)
            total_generated_predicts_home = home_total_generated > away_total_generated

            # ===== METRIC 3: Lead Duration =====
            # Count plays where each team had momentum lead
            home_lead_plays = sum(1 for dp in data_points if dp.home_momentum > 0)
            away_lead_plays = sum(1 for dp in data_points if dp.home_momentum < 0)
            lead_duration_predicts_home = home_lead_plays > away_lead_plays

            # ===== METRIC 4: Peak Momentum =====
            # Highest momentum achieved by each team
            home_peak = max((dp.home_momentum for dp in data_points), default=0)
            away_peak = max((abs(dp.home_momentum) for dp in data_points if dp.home_momentum < 0), default=0)
            peak_predicts_home = home_peak > away_peak

            # ===== METRIC 5: Average Momentum =====
            # Average momentum value throughout the game
            avg_momentum = sum(dp.home_momentum for dp in data_points) / len(data_points) if data_points else 0
            avg_predicts_home = avg_momentum > 0

            # Check each metric's prediction
            if (final_predicts_home == actual_home_won):
                metrics["final_momentum"]["correct"] += 1
            if (total_generated_predicts_home == actual_home_won):
                metrics["total_generated"]["correct"] += 1
            if (lead_duration_predicts_home == actual_home_won):
                metrics["lead_duration"]["correct"] += 1
            if (peak_predicts_home == actual_home_won):
                metrics["peak_momentum"]["correct"] += 1
            if (avg_predicts_home == actual_home_won):
                metrics["average_momentum"]["correct"] += 1

            # Calculate biggest swing in the game
            max_swing = 0
            max_swing_play = None
            for dp in data_points:
                if abs(dp.momentum_delta) > max_swing:
                    max_swing = abs(dp.momentum_delta)
                    max_swing_play = dp

            # Calculate average swing (excluding zero swings)
            swings = [abs(dp.momentum_delta) for dp in data_points if dp.momentum_delta != 0]
            avg_swing = sum(swings) / len(swings) if swings else 0

            # Calculate total volatility (sum of all absolute swings)
            total_volatility = sum(abs(dp.momentum_delta) for dp in data_points)

            # Use the best metric for the "predicted" field (we'll determine which is best)
            momentum_predicts_home = total_generated_predicts_home  # Use total generated as default

            game_analyses.append({
                "game_id": game.game_id,
                "week": game.week,
                "home_team": game.home_team,
                "away_team": game.away_team,
                "home_score": game.home_score,
                "away_score": game.away_score,
                "game_date": game.game_date.isoformat() if game.game_date else None,
                "final_home_momentum": round(final_home_momentum, 2),
                "home_total_generated": round(home_total_generated, 2),
                "away_total_generated": round(away_total_generated, 2),
                "home_lead_plays": home_lead_plays,
                "away_lead_plays": away_lead_plays,
                "actual_winner": game.home_team if actual_home_won else game.away_team,
                "momentum_predicted_winner": game.home_team if momentum_predicts_home else game.away_team,
                "predicted_correctly": momentum_predicts_home == actual_home_won,
                "biggest_swing": round(max_swing, 2),
                "biggest_swing_quarter": max_swing_play.quarter if max_swing_play else None,
                "biggest_swing_time": max_swing_play.time_remaining if max_swing_play else None,
                "average_swing": round(avg_swing, 2),
                "total_volatility": round(total_volatility, 2)
            })

            total_analyzed += 1

        except Exception as e:
            # Skip games that fail to analyze
            print(f"Error analyzing game {game.game_id}: {e}")
            continue

    # Calculate validation percentages for each metric
    validation_comparison = []
    for metric_name, metric_data in metrics.items():
        percentage = (metric_data["correct"] / total_analyzed * 100) if total_analyzed > 0 else 0
        validation_comparison.append({
            "metric": metric_name,
            "description": metric_data["description"],
            "correct_predictions": metric_data["correct"],
            "total_games": total_analyzed,
            "percentage": round(percentage, 1)
        })

    # Sort by accuracy (best predictor first)
    validation_comparison.sort(key=lambda x: x["percentage"], reverse=True)

    # Find the best metric
    best_metric = validation_comparison[0] if validation_comparison else None

    # Sort games by total volatility (most volatile first)
    games_by_volatility = sorted(game_analyses, key=lambda x: x["total_volatility"], reverse=True)

    # Calculate overall average swing
    all_avg_swings = [g["average_swing"] for g in game_analyses if g["average_swing"] > 0]
    overall_avg_swing = sum(all_avg_swings) / len(all_avg_swings) if all_avg_swings else 0

    return {
        "season": season,
        "total_games": len(games),
        "games_analyzed": total_analyzed,
        "validation_comparison": validation_comparison,
        "best_metric": best_metric,
        "validation": {
            "momentum_predicted_wins": best_metric["correct_predictions"] if best_metric else 0,
            "total_games": total_analyzed,
            "percentage": best_metric["percentage"] if best_metric else 0,
            "method": best_metric["description"] if best_metric else "N/A"
        },
        "games_by_volatility": games_by_volatility,
        "average_swing_per_game": round(overall_avg_swing, 2)
    }


@router.get("/teams/{season}")
def get_team_stats(season: int, db: Session = Depends(get_db)):
    """
    Get team statistics for a season.

    Returns:
        - Average momentum generated per game by team
        - Teams with biggest momentum swings
    """
    # Get all games for the season
    games = (
        db.query(Game)
        .filter(Game.season == season)
        .filter(Game.home_score.isnot(None))
        .filter(Game.away_score.isnot(None))
        .all()
    )

    if not games:
        raise HTTPException(status_code=404, detail=f"No games found for season {season}")

    calculator = MomentumCalculator(db)

    # Track team statistics
    team_stats: Dict[str, Dict[str, Any]] = {}

    for game in games:
        try:
            # Calculate momentum for this game
            data_points = calculator.calculate_game_momentum(game.game_id)

            if not data_points:
                continue

            # Initialize team stats if needed
            if game.home_team not in team_stats:
                team_stats[game.home_team] = {
                    "team": game.home_team,
                    "games": 0,
                    "total_momentum_generated": 0,
                    "total_swings": 0,
                    "biggest_swing": 0,
                    "biggest_swing_game": None
                }

            if game.away_team not in team_stats:
                team_stats[game.away_team] = {
                    "team": game.away_team,
                    "games": 0,
                    "total_momentum_generated": 0,
                    "total_swings": 0,
                    "biggest_swing": 0,
                    "biggest_swing_game": None
                }

            # Get final momentum values
            final_play = data_points[-1]

            # Update home team stats
            team_stats[game.home_team]["games"] += 1
            team_stats[game.home_team]["total_momentum_generated"] += abs(final_play.home_momentum)

            # Update away team stats
            team_stats[game.away_team]["games"] += 1
            team_stats[game.away_team]["total_momentum_generated"] += abs(final_play.away_momentum)

            # Calculate swings for each team
            for dp in data_points:
                swing = abs(dp.momentum_delta)

                # Track swing for the team that generated it
                if dp.momentum_delta > 0:  # Home team swing
                    team_stats[game.home_team]["total_swings"] += swing
                    if swing > team_stats[game.home_team]["biggest_swing"]:
                        team_stats[game.home_team]["biggest_swing"] = swing
                        team_stats[game.home_team]["biggest_swing_game"] = {
                            "game_id": game.game_id,
                            "opponent": game.away_team,
                            "week": game.week,
                            "swing": round(swing, 2)
                        }
                elif dp.momentum_delta < 0:  # Away team swing
                    team_stats[game.away_team]["total_swings"] += swing
                    if swing > team_stats[game.away_team]["biggest_swing"]:
                        team_stats[game.away_team]["biggest_swing"] = swing
                        team_stats[game.away_team]["biggest_swing_game"] = {
                            "game_id": game.game_id,
                            "opponent": game.home_team,
                            "week": game.week,
                            "swing": round(swing, 2)
                        }

        except Exception as e:
            # Skip games that fail to analyze
            print(f"Error analyzing game {game.game_id}: {e}")
            continue

    # Calculate averages
    team_results = []
    for team, stats in team_stats.items():
        if stats["games"] > 0:
            team_results.append({
                "team": team,
                "games_played": stats["games"],
                "avg_momentum_per_game": round(stats["total_momentum_generated"] / stats["games"], 2),
                "avg_swing_per_game": round(stats["total_swings"] / stats["games"], 2),
                "biggest_swing": round(stats["biggest_swing"], 2),
                "biggest_swing_game": stats["biggest_swing_game"]
            })

    # Sort by average momentum generated
    teams_by_avg_momentum = sorted(team_results, key=lambda x: x["avg_momentum_per_game"], reverse=True)

    # Sort by biggest swings
    teams_by_biggest_swing = sorted(team_results, key=lambda x: x["biggest_swing"], reverse=True)

    return {
        "season": season,
        "teams_by_avg_momentum": teams_by_avg_momentum,
        "teams_by_biggest_swing": teams_by_biggest_swing
    }
