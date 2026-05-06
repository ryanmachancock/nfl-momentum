"""
Data loader service for importing NFL play-by-play data from nfl_data_py.
"""
import nfl_data_py as nfl
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert
from datetime import datetime
from typing import Optional

from ..models import Game, Play


class DataLoader:
    """Handles loading NFL data from nfl_data_py into our database."""

    # Columns we need from the play-by-play data
    PBP_COLUMNS = [
        'game_id', 'play_id', 'qtr', 'time', 'down', 'ydstogo',
        'yardline_100', 'posteam', 'defteam', 'play_type', 'yards_gained',
        'desc', 'touchdown', 'pass_touchdown', 'rush_touchdown', 'return_touchdown',
        'interception', 'fumble_lost', 'sack', 'safety', 'penalty',
        'penalty_yards', 'first_down', 'third_down_converted',
        'third_down_failed', 'fourth_down_converted', 'fourth_down_failed',
        'field_goal_result', 'tackled_for_loss', 'home_team', 'away_team',
        'home_score', 'away_score', 'game_date', 'season', 'week', 'season_type',
        'home_wp', 'away_wp',  # Win probability
        # Score tracking (cumulative at time of play)
        'total_home_score', 'total_away_score', 'score_differential',
        # Field position and context
        'goal_to_go', 'drive',
        # Expected points
        'ep', 'epa',
        # Player names
        'passer_player_name', 'rusher_player_name', 'receiver_player_name',
        'interception_player_name', 'sack_player_name', 'fumbled_1_player_name',
        'fumble_recovery_1_player_name', 'td_player_name', 'kicker_player_name',
        'safety_player_name', 'punt_returner_player_name', 'kickoff_returner_player_name'
    ]

    def __init__(self, db: Session):
        self.db = db

    def load_season(self, season: int) -> dict:
        """
        Load all games and plays for a given season.

        Returns:
            dict with counts of games and plays loaded
        """
        print(f"Loading play-by-play data for {season} season...")

        # Load play-by-play data
        pbp = nfl.import_pbp_data([season])

        # Filter to columns we need (some may not exist in older seasons)
        available_cols = [c for c in self.PBP_COLUMNS if c in pbp.columns]
        pbp = pbp[available_cols]

        # Get unique games
        games_df = pbp.groupby('game_id').first().reset_index()

        games_loaded = 0
        plays_loaded = 0

        # Process each game
        for _, game_row in games_df.iterrows():
            game_id = game_row['game_id']

            # Check if game already exists
            existing = self.db.query(Game).filter(Game.game_id == game_id).first()
            if existing:
                print(f"  Skipping {game_id} (already exists)")
                continue

            # Create game record
            game = Game(
                game_id=game_id,
                season=int(game_row.get('season', season)),
                week=int(game_row.get('week', 0)),
                game_type=self._map_season_type(game_row.get('season_type', 'REG')),
                home_team=game_row.get('home_team', ''),
                away_team=game_row.get('away_team', ''),
                home_score=self._safe_int(game_row.get('home_score')),
                away_score=self._safe_int(game_row.get('away_score')),
                game_date=self._parse_date(game_row.get('game_date'))
            )
            self.db.add(game)
            games_loaded += 1

            # Get plays for this game
            game_plays = pbp[pbp['game_id'] == game_id].sort_values('play_id')

            for _, play_row in game_plays.iterrows():
                play = Play(
                    game_id=game_id,
                    play_id=int(play_row['play_id']),
                    quarter=self._safe_int(play_row.get('qtr')),
                    time_remaining=str(play_row.get('time', '')),
                    down=self._safe_int(play_row.get('down')),
                    yards_to_go=self._safe_int(play_row.get('ydstogo')),
                    yard_line=self._safe_int(play_row.get('yardline_100')),
                    posteam=play_row.get('posteam'),
                    defteam=play_row.get('defteam'),
                    # Score tracking
                    home_score=self._safe_int(play_row.get('total_home_score')),
                    away_score=self._safe_int(play_row.get('total_away_score')),
                    score_differential=self._safe_int(play_row.get('score_differential')),
                    # Field position and context
                    yardline_100=self._safe_int(play_row.get('yardline_100')),
                    goal_to_go=self._safe_bool(play_row.get('goal_to_go')),
                    drive_number=self._safe_int(play_row.get('drive')),
                    # Expected points
                    ep=self._safe_float(play_row.get('ep')),
                    epa=self._safe_float(play_row.get('epa')),
                    # Play info
                    play_type=play_row.get('play_type'),
                    yards_gained=self._safe_int(play_row.get('yards_gained')),
                    description=str(play_row.get('desc', ''))[:500],
                    touchdown=self._safe_bool(play_row.get('touchdown')),
                    pass_touchdown=self._safe_bool(play_row.get('pass_touchdown')),
                    rush_touchdown=self._safe_bool(play_row.get('rush_touchdown')),
                    return_touchdown=self._safe_bool(play_row.get('return_touchdown')),
                    interception=self._safe_bool(play_row.get('interception')),
                    fumble_lost=self._safe_bool(play_row.get('fumble_lost')),
                    sack=self._safe_bool(play_row.get('sack')),
                    safety=self._safe_bool(play_row.get('safety')),
                    penalty=self._safe_bool(play_row.get('penalty')),
                    penalty_yards=self._safe_int(play_row.get('penalty_yards')),
                    first_down=self._safe_bool(play_row.get('first_down')),
                    third_down_converted=self._safe_bool(play_row.get('third_down_converted')),
                    third_down_failed=self._safe_bool(play_row.get('third_down_failed')),
                    fourth_down_converted=self._safe_bool(play_row.get('fourth_down_converted')),
                    fourth_down_failed=self._safe_bool(play_row.get('fourth_down_failed')),
                    field_goal_result=play_row.get('field_goal_result'),
                    tackled_for_loss=self._safe_bool(play_row.get('tackled_for_loss')),
                    home_wp=self._safe_float(play_row.get('home_wp')),
                    away_wp=self._safe_float(play_row.get('away_wp')),
                    # Player names
                    passer_player_name=self._safe_str(play_row.get('passer_player_name')),
                    rusher_player_name=self._safe_str(play_row.get('rusher_player_name')),
                    receiver_player_name=self._safe_str(play_row.get('receiver_player_name')),
                    interception_player_name=self._safe_str(play_row.get('interception_player_name')),
                    sack_player_name=self._safe_str(play_row.get('sack_player_name')),
                    fumbled_player_name=self._safe_str(play_row.get('fumbled_1_player_name')),
                    fumble_recovery_player_name=self._safe_str(play_row.get('fumble_recovery_1_player_name')),
                    td_player_name=self._safe_str(play_row.get('td_player_name')),
                    kicker_player_name=self._safe_str(play_row.get('kicker_player_name')),
                    safety_player_name=self._safe_str(play_row.get('safety_player_name')),
                    punt_returner_player_name=self._safe_str(play_row.get('punt_returner_player_name')),
                    kickoff_returner_player_name=self._safe_str(play_row.get('kickoff_returner_player_name'))
                )
                self.db.add(play)
                plays_loaded += 1

            # Commit after each game to avoid memory issues
            self.db.commit()
            print(f"  Loaded {game_id}: {game.away_team} @ {game.home_team}")

        return {
            "season": season,
            "games_loaded": games_loaded,
            "plays_loaded": plays_loaded
        }

    def load_single_game(self, game_id: str, season: int) -> Optional[Game]:
        """Load a single game by ID."""
        pbp = nfl.import_pbp_data([season])
        game_pbp = pbp[pbp['game_id'] == game_id]

        if game_pbp.empty:
            return None

        # Same logic as load_season but for one game
        game_row = game_pbp.iloc[0]

        game = Game(
            game_id=game_id,
            season=season,
            week=int(game_row.get('week', 0)),
            game_type=self._map_season_type(game_row.get('season_type', 'REG')),
            home_team=game_row.get('home_team', ''),
            away_team=game_row.get('away_team', ''),
            home_score=self._safe_int(game_row.get('home_score')),
            away_score=self._safe_int(game_row.get('away_score')),
            game_date=self._parse_date(game_row.get('game_date'))
        )
        self.db.add(game)

        for _, play_row in game_pbp.sort_values('play_id').iterrows():
            play = Play(
                game_id=game_id,
                play_id=int(play_row['play_id']),
                quarter=self._safe_int(play_row.get('qtr')),
                time_remaining=str(play_row.get('time', '')),
                down=self._safe_int(play_row.get('down')),
                yards_to_go=self._safe_int(play_row.get('ydstogo')),
                yard_line=self._safe_int(play_row.get('yardline_100')),
                posteam=play_row.get('posteam'),
                defteam=play_row.get('defteam'),
                # Score tracking
                home_score=self._safe_int(play_row.get('total_home_score')),
                away_score=self._safe_int(play_row.get('total_away_score')),
                score_differential=self._safe_int(play_row.get('score_differential')),
                # Field position and context
                yardline_100=self._safe_int(play_row.get('yardline_100')),
                goal_to_go=self._safe_bool(play_row.get('goal_to_go')),
                drive_number=self._safe_int(play_row.get('drive')),
                # Expected points
                ep=self._safe_float(play_row.get('ep')),
                epa=self._safe_float(play_row.get('epa')),
                # Play info
                play_type=play_row.get('play_type'),
                yards_gained=self._safe_int(play_row.get('yards_gained')),
                description=str(play_row.get('desc', ''))[:500],
                touchdown=self._safe_bool(play_row.get('touchdown')),
                pass_touchdown=self._safe_bool(play_row.get('pass_touchdown')),
                rush_touchdown=self._safe_bool(play_row.get('rush_touchdown')),
                return_touchdown=self._safe_bool(play_row.get('return_touchdown')),
                interception=self._safe_bool(play_row.get('interception')),
                fumble_lost=self._safe_bool(play_row.get('fumble_lost')),
                sack=self._safe_bool(play_row.get('sack')),
                safety=self._safe_bool(play_row.get('safety')),
                penalty=self._safe_bool(play_row.get('penalty')),
                penalty_yards=self._safe_int(play_row.get('penalty_yards')),
                first_down=self._safe_bool(play_row.get('first_down')),
                third_down_converted=self._safe_bool(play_row.get('third_down_converted')),
                third_down_failed=self._safe_bool(play_row.get('third_down_failed')),
                fourth_down_converted=self._safe_bool(play_row.get('fourth_down_converted')),
                fourth_down_failed=self._safe_bool(play_row.get('fourth_down_failed')),
                field_goal_result=play_row.get('field_goal_result'),
                tackled_for_loss=self._safe_bool(play_row.get('tackled_for_loss')),
                home_wp=self._safe_float(play_row.get('home_wp')),
                away_wp=self._safe_float(play_row.get('away_wp')),
                # Player names
                passer_player_name=self._safe_str(play_row.get('passer_player_name')),
                rusher_player_name=self._safe_str(play_row.get('rusher_player_name')),
                receiver_player_name=self._safe_str(play_row.get('receiver_player_name')),
                interception_player_name=self._safe_str(play_row.get('interception_player_name')),
                sack_player_name=self._safe_str(play_row.get('sack_player_name')),
                fumbled_player_name=self._safe_str(play_row.get('fumbled_1_player_name')),
                fumble_recovery_player_name=self._safe_str(play_row.get('fumble_recovery_1_player_name')),
                td_player_name=self._safe_str(play_row.get('td_player_name')),
                kicker_player_name=self._safe_str(play_row.get('kicker_player_name')),
                safety_player_name=self._safe_str(play_row.get('safety_player_name')),
                punt_returner_player_name=self._safe_str(play_row.get('punt_returner_player_name')),
                kickoff_returner_player_name=self._safe_str(play_row.get('kickoff_returner_player_name'))
            )
            self.db.add(play)

        self.db.commit()
        return game

    def get_available_seasons(self) -> list[int]:
        """Get list of seasons available from nfl_data_py."""
        # nflfastR has data from 1999-present
        current_year = datetime.now().year
        return list(range(1999, current_year + 1))

    @staticmethod
    def _safe_int(value) -> Optional[int]:
        """Safely convert to int, handling NaN and None."""
        if pd.isna(value):
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _safe_float(value) -> Optional[float]:
        """Safely convert to float, handling NaN and None."""
        if pd.isna(value):
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _safe_bool(value) -> bool:
        """Safely convert to bool, handling NaN as False (not True!)."""
        if pd.isna(value):
            return False
        # nflfastR uses 0/1 integers or floats
        try:
            return bool(int(value))
        except (ValueError, TypeError):
            return False

    @staticmethod
    def _safe_str(value, max_length: int = 50) -> Optional[str]:
        """Safely convert to string, handling NaN and None."""
        if pd.isna(value) or value is None:
            return None
        s = str(value).strip()
        return s[:max_length] if s else None

    @staticmethod
    def _parse_date(value) -> Optional[datetime]:
        """Parse date string to datetime."""
        if pd.isna(value):
            return None
        try:
            return pd.to_datetime(value).date()
        except Exception:
            return None

    @staticmethod
    def _map_season_type(season_type: str) -> str:
        """Map nflfastR season_type to our format."""
        mapping = {
            'REG': 'REG',
            'POST': 'POST',
            'WC': 'WC',
            'DIV': 'DIV',
            'CON': 'CON',
            'SB': 'SB'
        }
        return mapping.get(str(season_type).upper(), 'REG')
