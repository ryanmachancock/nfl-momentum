"""
Backfill script to load historical NFL data.

Usage:
    python -m app.scripts.backfill --seasons 2024 2023 2022
    python -m app.scripts.backfill --all-recent  # Last 5 years
"""
import argparse
import sys
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(__file__).replace('\\', '/').rsplit('/', 3)[0])

from app.database import SessionLocal, init_db
from app.services import DataLoader, MomentumCalculator


def backfill_seasons(seasons: list[int], calculate_momentum: bool = True):
    """Load data for specified seasons."""
    init_db()
    db = SessionLocal()

    try:
        loader = DataLoader(db)

        for season in seasons:
            print(f"\n{'='*50}")
            print(f"Loading {season} season...")
            print('='*50)

            try:
                result = loader.load_season(season)
                print(f"\nLoaded {result['games_loaded']} games, {result['plays_loaded']} plays")

                if calculate_momentum and result['games_loaded'] > 0:
                    print("Calculating momentum for new games...")
                    calculator = MomentumCalculator(db)

                    # Get games from this season
                    from app.models import Game
                    games = db.query(Game).filter(Game.season == season).all()

                    for game in games:
                        calculator.calculate_game_momentum(game.game_id)
                        print(f"  Calculated: {game.game_id}")

            except Exception as e:
                print(f"Error loading {season}: {e}")
                continue

        print("\n" + "="*50)
        print("Backfill complete!")
        print("="*50)

    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description="Backfill NFL play-by-play data")
    parser.add_argument(
        '--seasons',
        type=int,
        nargs='+',
        help='Specific seasons to load (e.g., 2024 2023 2022)'
    )
    parser.add_argument(
        '--all-recent',
        action='store_true',
        help='Load last 5 years of data'
    )
    parser.add_argument(
        '--no-momentum',
        action='store_true',
        help='Skip momentum calculation'
    )

    args = parser.parse_args()

    if args.all_recent:
        current_year = datetime.now().year
        seasons = list(range(current_year, current_year - 5, -1))
    elif args.seasons:
        seasons = args.seasons
    else:
        # Default to current year
        seasons = [datetime.now().year]

    print(f"Will load seasons: {seasons}")
    backfill_seasons(seasons, calculate_momentum=not args.no_momentum)


if __name__ == "__main__":
    main()
