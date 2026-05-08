"""
Momentum calculation engine for NFL games.

Based on academic research showing momentum is real in NFL games,
this module calculates an event-based momentum score from play-by-play data.
"""
from dataclasses import dataclass
from typing import Optional, List, Dict, Tuple
import re
from sqlalchemy.orm import Session

from ..models import Game, Play
from ..schemas import MomentumDataPoint


@dataclass
class MomentumEvent:
    """Represents a momentum-affecting event."""
    name: str
    points: float
    team: str  # 'offense' or 'defense' - who benefits
    is_turnover: bool = False  # For field position multiplier
    is_conversion: bool = False  # For down & distance multiplier


class MomentumCalculator:
    """
    Calculates momentum scores for NFL games based on play-by-play events.

    The algorithm:
    1. Each play generates momentum points for the benefiting team
    2. Game-state multipliers weight events by leverage (time, score, field position, down & distance)
    3. Momentum decays over real time (not per-play)
    4. Consecutive positive events get a streak multiplier
    5. Final score normalized to -100 to +100 (home team perspective)
    """

    # Momentum point values for different events
    MOMENTUM_POINTS = {
        # Touchdowns (to offense/scoring team)
        'passing_td': 15,
        'rushing_td': 15,
        'defensive_return_td': 25,  # Pick-6, fumble return, etc.

        # Turnovers (to defense/receiving team)
        'interception': 12,
        'fumble_lost': 10,
        'turnover_on_downs': 8,

        # Big plays - offense (scaled by yardage)
        'big_play_base': 3,      # 20-29 yards base
        'big_play_per_yard': 0.15,  # Additional points per yard over 20
        'explosive_threshold': 40,  # 40+ yards = "Explosive"
        'first_down': 2,
        'third_down_conversion': 3,
        'fourth_down_conversion': 5,

        # Defensive stops
        'sack': 5,
        'tackle_for_loss': 3,
        'third_down_stop': 3,
        'fourth_down_stop': 6,
        'safety': 15,

        # Field goals
        'field_goal_made': 5,
        'field_goal_missed': 7,  # To defense
        'field_goal_blocked': 10,  # To defense

        # Penalties (10+ yards)
        'big_penalty': 3,
    }

    # Time-based decay - momentum decays ~30% per minute
    # Using decay = 0.995 ^ seconds_elapsed
    DECAY_BASE = 0.995

    # Streak multiplier settings
    MAX_STREAK_MULTIPLIER = 1.5
    STREAK_INCREMENT = 0.1

    # Timeout effects (based on research showing ~11% momentum decline after breaks)
    # Reference: Weimer et al. (2023) "A causal approach for detecting team-level momentum"
    TIMEOUT_MOMENTUM_DECAY = 0.88  # 12% reduction to opponent's momentum
    TIMEOUT_CALLING_BOOST = 1.03   # 3% boost to calling team (reset/regroup benefit)

    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _detect_timeout(play: Play) -> Optional[str]:
        """
        Detect if a play is a timeout and which team called it.

        Args:
            play: The play object

        Returns:
            Team abbreviation that called the timeout, or None if not a timeout
        """
        if not play.description:
            return None

        desc = play.description.upper()
        if 'TIMEOUT' not in desc:
            return None

        # Parse team from description like "Timeout #2 by ATL at 01:09."
        # Pattern: "TIMEOUT ... BY <TEAM>"
        match = re.search(r'TIMEOUT.*BY\s+([A-Z]{2,3})', desc)
        if match:
            return match.group(1)
        return None

    @staticmethod
    def _parse_time_to_seconds(quarter: int, time_remaining: str) -> int:
        """
        Convert quarter and time_remaining to total elapsed seconds.

        Args:
            quarter: Quarter number (1-4, or 5 for OT)
            time_remaining: Time string in format "MM:SS"

        Returns:
            Total elapsed seconds from start of game
        """
        # Parse time_remaining (format: "MM:SS")
        match = re.match(r'(\d+):(\d+)', time_remaining or "0:00")
        if match:
            minutes = int(match.group(1))
            seconds = int(match.group(2))
            time_left_in_quarter = minutes * 60 + seconds
        else:
            time_left_in_quarter = 0

        # Each quarter is 15 minutes (900 seconds)
        quarter_duration = 900

        # Calculate elapsed time
        if quarter <= 4:
            # Regular time
            completed_quarters = quarter - 1
            elapsed_in_quarter = quarter_duration - time_left_in_quarter
            total_elapsed = (completed_quarters * quarter_duration) + elapsed_in_quarter
        else:
            # Overtime - treat as continuation of 4th quarter
            total_elapsed = (4 * quarter_duration) + (quarter_duration - time_left_in_quarter)

        return total_elapsed

    def _calculate_game_state_multiplier(
        self,
        play: Play,
        event: MomentumEvent
    ) -> float:
        """
        Calculate the game-state multiplier for an event based on leverage.

        Considers:
        - Time (quarter): Later in game = higher leverage
        - Score differential: Close games = higher leverage
        - Field position (for turnovers): Turnovers near goal line = higher value
        - Down & distance (for conversions): Harder conversions = higher value

        Args:
            play: The play object with game state information
            event: The momentum event

        Returns:
            Combined multiplier (typically 0.85 - 2.0+)
        """
        multiplier = 1.0

        # 1. TIME MULTIPLIER - Events in Q4 matter more
        # Q1: 1.0x, Q2: 1.15x, Q3: 1.3x, Q4: 1.45x
        quarter = play.quarter or 1
        time_multiplier = 1 + (quarter - 1) * 0.15
        multiplier *= time_multiplier

        # 2. SCORE DIFFERENTIAL MULTIPLIER - Close games have higher leverage
        home_score = play.home_score or 0
        away_score = play.away_score or 0
        score_diff = abs(home_score - away_score)

        if score_diff <= 7:
            score_multiplier = 1.3  # One score game
        elif score_diff <= 14:
            score_multiplier = 1.15  # Two score game
        else:
            score_multiplier = 0.85  # Blowout

        multiplier *= score_multiplier

        # 3. FIELD POSITION MULTIPLIER - For turnovers only
        # Turnovers near opponent's goal line prevent likely TDs
        if event.is_turnover and play.yardline_100 is not None:
            # yardline_100 is yards from opponent's endzone (100 = own goal line, 0 = opponent goal line)
            # Turnovers at yardline_100 = 10 (near opponent goal) are worth more
            # Formula: 1 + (100 - yardline_100) / 100
            # At yardline_100 = 10: 1 + 90/100 = 1.9x
            # At yardline_100 = 50: 1 + 50/100 = 1.5x
            # At yardline_100 = 90: 1 + 10/100 = 1.1x
            field_position_multiplier = 1 + (100 - play.yardline_100) / 100
            multiplier *= field_position_multiplier

        # 4. DOWN & DISTANCE MULTIPLIER - For conversions only
        # Harder conversions (4th & 15) are worth more than easy ones (4th & 1)
        if event.is_conversion and play.yards_to_go is not None:
            # Formula: 1 + yards_to_go / 20
            # 4th & 1: 1 + 1/20 = 1.05x
            # 4th & 5: 1 + 5/20 = 1.25x
            # 4th & 15: 1 + 15/20 = 1.75x
            down_distance_multiplier = 1 + play.yards_to_go / 20
            multiplier *= down_distance_multiplier

        return multiplier

    def calculate_game_momentum(self, game_id: str) -> list[MomentumDataPoint]:
        """
        Calculate momentum for all plays in a game.

        Returns:
            List of MomentumDataPoint with momentum values for each play
        """
        # Get game and plays
        game = self.db.query(Game).filter(Game.game_id == game_id).first()
        if not game:
            raise ValueError(f"Game {game_id} not found")

        plays = (
            self.db.query(Play)
            .filter(Play.game_id == game_id)
            .order_by(Play.play_id)
            .all()
        )

        if not plays:
            return []

        home_team = game.home_team
        away_team = game.away_team

        # Track running momentum
        home_momentum = 0.0
        away_momentum = 0.0

        # Track streaks
        home_streak = 0
        away_streak = 0

        # Track last play time for time-based decay
        last_game_time = 0  # seconds elapsed

        data_points = []

        for play in plays:
            # Calculate elapsed time for this play
            current_game_time = self._parse_time_to_seconds(
                play.quarter or 1,
                play.time_remaining or "15:00"
            )

            # Calculate time-based decay
            # Apply decay based on actual time elapsed since last play
            if last_game_time > 0:
                seconds_elapsed = current_game_time - last_game_time
                # Ensure non-negative (handles clock resets at quarter changes)
                if seconds_elapsed > 0:
                    decay_factor = self.DECAY_BASE ** seconds_elapsed
                    home_momentum *= decay_factor
                    away_momentum *= decay_factor

            last_game_time = current_game_time

            # Check for timeout and apply momentum-breaking effect
            timeout_team = self._detect_timeout(play)
            timeout_event_desc = None
            if timeout_team:
                # Research shows timeouts break momentum of the team on a run
                # Apply decay to opponent's momentum, slight boost to calling team
                if timeout_team == home_team:
                    # Home team called timeout - likely trying to stop away momentum
                    away_momentum *= self.TIMEOUT_MOMENTUM_DECAY
                    home_momentum *= self.TIMEOUT_CALLING_BOOST
                    timeout_event_desc = f"Timeout by {home_team}"
                elif timeout_team == away_team:
                    # Away team called timeout - likely trying to stop home momentum
                    home_momentum *= self.TIMEOUT_MOMENTUM_DECAY
                    away_momentum *= self.TIMEOUT_CALLING_BOOST
                    timeout_event_desc = f"Timeout by {away_team}"

                # Timeouts also reset momentum streaks (breaks the flow)
                home_streak = 0
                away_streak = 0

            # Detect events and calculate momentum delta
            events = self._detect_events(play, home_team, away_team)

            # Calculate raw momentum change with game-state multipliers
            home_delta = 0.0
            away_delta = 0.0

            for event in events:
                # Apply game-state multiplier to the event points
                multiplier = self._calculate_game_state_multiplier(play, event)
                adjusted_points = event.points * multiplier

                if event.team == home_team:
                    home_delta += adjusted_points
                elif event.team == away_team:
                    away_delta += adjusted_points

            # Apply streak multipliers
            if home_delta > 0:
                home_streak += 1
                away_streak = 0
                streak_multiplier = min(
                    1 + (self.STREAK_INCREMENT * (home_streak - 1)),
                    self.MAX_STREAK_MULTIPLIER
                )
                home_delta *= streak_multiplier
            elif away_delta > 0:
                away_streak += 1
                home_streak = 0
                streak_multiplier = min(
                    1 + (self.STREAK_INCREMENT * (away_streak - 1)),
                    self.MAX_STREAK_MULTIPLIER
                )
                away_delta *= streak_multiplier

            # Add new momentum (decay already applied above)
            home_momentum += home_delta
            away_momentum += away_delta

            # Update play record
            play.home_momentum = home_momentum
            play.away_momentum = away_momentum
            play.momentum_delta = home_delta - away_delta

            # Determine if this is a significant event
            # Timeouts are always significant (strategic momentum breakers)
            is_significant = abs(home_delta - away_delta) >= 10 or timeout_event_desc is not None

            # Build event description
            event_desc = None
            if timeout_event_desc:
                event_desc = timeout_event_desc
            elif events:
                event_desc = ", ".join([e.name for e in events])

            data_points.append(MomentumDataPoint(
                play_id=play.play_id,
                quarter=play.quarter or 1,
                time_remaining=play.time_remaining or "15:00",
                home_momentum=round(home_momentum, 2),
                away_momentum=round(away_momentum, 2),
                momentum_delta=round(home_delta - away_delta, 2),
                home_wp=play.home_wp,
                away_wp=play.away_wp,
                home_score=play.home_score or 0,
                away_score=play.away_score or 0,
                yardline_100=play.yardline_100,
                down=play.down,
                yards_to_go=play.yards_to_go,
                event_description=event_desc,
                is_significant=is_significant
            ))

        return data_points

    def _detect_events(self, play: Play, home_team: str, away_team: str) -> list[MomentumEvent]:
        """Detect momentum-affecting events from a play."""
        events = []

        posteam = play.posteam  # Team with possession
        defteam = play.defteam  # Defending team

        # Skip plays without teams (timeouts, end of quarter, etc.)
        if not posteam or not defteam:
            return events

        # Skip metadata rows (END QUARTER, END GAME, etc.)
        # These have all event flags incorrectly set to true in nflfastR data
        if play.description:
            desc_upper = play.description.upper()
            if 'END QUARTER' in desc_upper or 'END GAME' in desc_upper or 'END OF' in desc_upper:
                return events

        # === TOUCHDOWNS ===
        if play.touchdown:
            td_player = play.td_player_name or ""
            if play.return_touchdown:
                # Defensive/special teams TD - defense gets huge boost
                # Check for punt/kickoff returner
                returner = play.punt_returner_player_name or play.kickoff_returner_player_name or play.interception_player_name or td_player
                name = f"Return TD ({returner})" if returner else "Defensive/Return TD"
                events.append(MomentumEvent(
                    name=name,
                    points=self.MOMENTUM_POINTS['defensive_return_td'],
                    team=defteam
                ))
            elif play.pass_touchdown:
                passer = play.passer_player_name or ""
                receiver = play.receiver_player_name or ""
                if passer and receiver:
                    name = f"Passing TD ({passer} to {receiver})"
                elif td_player:
                    name = f"Passing TD ({td_player})"
                else:
                    name = "Passing TD"
                events.append(MomentumEvent(
                    name=name,
                    points=self.MOMENTUM_POINTS['passing_td'],
                    team=posteam
                ))
            elif play.rush_touchdown:
                rusher = play.rusher_player_name or td_player
                name = f"Rushing TD ({rusher})" if rusher else "Rushing TD"
                events.append(MomentumEvent(
                    name=name,
                    points=self.MOMENTUM_POINTS['rushing_td'],
                    team=posteam
                ))
            else:
                # Generic TD
                name = f"Touchdown ({td_player})" if td_player else "Touchdown"
                events.append(MomentumEvent(
                    name=name,
                    points=self.MOMENTUM_POINTS['passing_td'],
                    team=posteam
                ))

        # === TURNOVERS ===
        if play.interception:
            interceptor = play.interception_player_name
            name = f"INT ({interceptor})" if interceptor else "Interception"
            events.append(MomentumEvent(
                name=name,
                points=self.MOMENTUM_POINTS['interception'],
                team=defteam,
                is_turnover=True
            ))

        if play.fumble_lost:
            fumbler = play.fumbled_player_name
            recoverer = play.fumble_recovery_player_name
            if fumbler and recoverer:
                name = f"Fumble ({fumbler}, rec. {recoverer})"
            elif recoverer:
                name = f"Fumble (rec. {recoverer})"
            else:
                name = "Fumble Lost"
            events.append(MomentumEvent(
                name=name,
                points=self.MOMENTUM_POINTS['fumble_lost'],
                team=defteam,
                is_turnover=True
            ))

        # === FOURTH DOWN ===
        if play.fourth_down_converted:
            events.append(MomentumEvent(
                name="4th Down Conversion",
                points=self.MOMENTUM_POINTS['fourth_down_conversion'],
                team=posteam,
                is_conversion=True
            ))
        elif play.fourth_down_failed:
            events.append(MomentumEvent(
                name="4th Down Stop",
                points=self.MOMENTUM_POINTS['fourth_down_stop'],
                team=defteam
            ))

        # === THIRD DOWN ===
        if play.third_down_converted:
            events.append(MomentumEvent(
                name="3rd Down Conversion",
                points=self.MOMENTUM_POINTS['third_down_conversion'],
                team=posteam,
                is_conversion=True
            ))
        elif play.third_down_failed:
            events.append(MomentumEvent(
                name="3rd Down Stop",
                points=self.MOMENTUM_POINTS['third_down_stop'],
                team=defteam
            ))

        # === DEFENSIVE PLAYS ===
        if play.sack:
            sacker = play.sack_player_name
            name = f"Sack ({sacker})" if sacker else "Sack"
            events.append(MomentumEvent(
                name=name,
                points=self.MOMENTUM_POINTS['sack'],
                team=defteam
            ))

        if play.tackled_for_loss and not play.sack:  # Avoid double-counting
            events.append(MomentumEvent(
                name="Tackle for Loss",
                points=self.MOMENTUM_POINTS['tackle_for_loss'],
                team=defteam
            ))

        if play.safety:
            safety_player = play.safety_player_name
            name = f"Safety ({safety_player})" if safety_player else "Safety"
            events.append(MomentumEvent(
                name=name,
                points=self.MOMENTUM_POINTS['safety'],
                team=defteam
            ))

        # === FIELD GOALS ===
        if play.field_goal_result:
            kicker = play.kicker_player_name
            if play.field_goal_result == 'made':
                name = f"FG Made ({kicker})" if kicker else "Field Goal Made"
                events.append(MomentumEvent(
                    name=name,
                    points=self.MOMENTUM_POINTS['field_goal_made'],
                    team=posteam
                ))
            elif play.field_goal_result == 'missed':
                name = f"FG Missed ({kicker})" if kicker else "Field Goal Missed"
                events.append(MomentumEvent(
                    name=name,
                    points=self.MOMENTUM_POINTS['field_goal_missed'],
                    team=defteam
                ))
            elif play.field_goal_result == 'blocked':
                name = f"FG Blocked ({kicker})" if kicker else "Field Goal Blocked"
                events.append(MomentumEvent(
                    name=name,
                    points=self.MOMENTUM_POINTS['field_goal_blocked'],
                    team=defteam
                ))

        # === BIG PLAYS ===
        # Scaled momentum: bigger plays = more impact
        # 20-39 yards: "Big Play", 40+: "Explosive Play"
        yards = play.yards_gained or 0
        if yards >= 20 and not play.touchdown:  # Don't double count TDs
            # Calculate scaled points: base + (yards over 20) * per_yard_bonus
            # 20 yards = 3 points, 30 yards = 4.5 points, 40 yards = 6 points, 50 yards = 7.5 points
            base_points = self.MOMENTUM_POINTS['big_play_base']
            per_yard_bonus = self.MOMENTUM_POINTS['big_play_per_yard']
            scaled_points = base_points + (yards - 20) * per_yard_bonus

            # Find the playmaker
            playmaker = play.receiver_player_name or play.rusher_player_name

            # Label based on yardage threshold
            if yards >= self.MOMENTUM_POINTS['explosive_threshold']:
                name = f"Explosive Play ({yards} yds, {playmaker})" if playmaker else f"Explosive Play ({yards} yds)"
            else:
                name = f"Big Play ({yards} yds, {playmaker})" if playmaker else f"Big Play ({yards} yds)"

            events.append(MomentumEvent(
                name=name,
                points=scaled_points,
                team=posteam
            ))

        # === FIRST DOWNS (only if no bigger event) ===
        if play.first_down and not events:
            events.append(MomentumEvent(
                name="First Down",
                points=self.MOMENTUM_POINTS['first_down'],
                team=posteam
            ))

        # === BIG PENALTIES ===
        if play.penalty and play.penalty_yards and abs(play.penalty_yards) >= 10:
            # Penalty yards are negative for the penalized team
            if play.penalty_yards > 0:
                # Offense benefited
                events.append(MomentumEvent(
                    name=f"Penalty ({play.penalty_yards} yds)",
                    points=self.MOMENTUM_POINTS['big_penalty'],
                    team=posteam
                ))
            else:
                # Defense benefited
                events.append(MomentumEvent(
                    name=f"Penalty ({abs(play.penalty_yards)} yds)",
                    points=self.MOMENTUM_POINTS['big_penalty'],
                    team=defteam
                ))

        return events

    def detect_comebacks(
        self,
        data_points: List[MomentumDataPoint],
        home_team: str,
        away_team: str,
        deficit_threshold: float = 40.0,
        max_plays_for_comeback: int = 30
    ) -> List[Dict]:
        """
        Detect comeback events in the game momentum data.

        A comeback is defined as:
        1. Team was trailing in momentum by deficit_threshold or more
        2. Team then gained the lead in momentum
        3. The swing happened within max_plays_for_comeback plays

        Args:
            data_points: List of momentum data points
            home_team: Home team abbreviation
            away_team: Away team abbreviation
            deficit_threshold: Minimum momentum deficit to qualify as comeback (default: 40.0)
            max_plays_for_comeback: Maximum number of plays for comeback window (default: 30)

        Returns:
            List of comeback events with details
        """
        if not data_points:
            return []

        comebacks = []

        # Track potential comeback start points for each team
        # Format: {'team': team_name, 'start_idx': index, 'deficit': deficit_value}
        home_deficit_start = None
        away_deficit_start = None

        for i, dp in enumerate(data_points):
            # Calculate net momentum (positive = home advantage, negative = away advantage)
            net_momentum = dp.home_momentum - dp.away_momentum

            # Check for HOME team comeback
            # Home team is in deficit when net_momentum is significantly negative
            if net_momentum <= -deficit_threshold:
                # Home team is trailing, record this as potential comeback start
                if home_deficit_start is None or net_momentum < home_deficit_start['deficit']:
                    home_deficit_start = {
                        'team': home_team,
                        'start_idx': i,
                        'deficit': net_momentum,
                        'start_play_id': dp.play_id,
                        'start_quarter': dp.quarter,
                        'start_time': dp.time_remaining
                    }
            elif net_momentum > 0 and home_deficit_start is not None:
                # Home team now has the lead! Check if comeback conditions are met
                plays_elapsed = i - home_deficit_start['start_idx']
                if plays_elapsed <= max_plays_for_comeback:
                    # Valid comeback!
                    momentum_swing = net_momentum - home_deficit_start['deficit']
                    comebacks.append({
                        'team': home_team,
                        'start_play_id': home_deficit_start['start_play_id'],
                        'end_play_id': dp.play_id,
                        'momentum_deficit': round(abs(home_deficit_start['deficit']), 2),
                        'final_momentum': round(net_momentum, 2),
                        'momentum_swing': round(momentum_swing, 2),
                        'quarter': dp.quarter,
                        'start_quarter': home_deficit_start['start_quarter'],
                        'start_time': home_deficit_start['start_time'],
                        'end_time': dp.time_remaining,
                        'plays_elapsed': plays_elapsed
                    })
                # Reset after comeback is recorded or window passed
                home_deficit_start = None

            # Check for AWAY team comeback
            # Away team is in deficit when net_momentum is significantly positive
            if net_momentum >= deficit_threshold:
                # Away team is trailing, record this as potential comeback start
                if away_deficit_start is None or net_momentum > away_deficit_start['deficit']:
                    away_deficit_start = {
                        'team': away_team,
                        'start_idx': i,
                        'deficit': net_momentum,
                        'start_play_id': dp.play_id,
                        'start_quarter': dp.quarter,
                        'start_time': dp.time_remaining
                    }
            elif net_momentum < 0 and away_deficit_start is not None:
                # Away team now has the lead! Check if comeback conditions are met
                plays_elapsed = i - away_deficit_start['start_idx']
                if plays_elapsed <= max_plays_for_comeback:
                    # Valid comeback!
                    momentum_swing = abs(net_momentum - away_deficit_start['deficit'])
                    comebacks.append({
                        'team': away_team,
                        'start_play_id': away_deficit_start['start_play_id'],
                        'end_play_id': dp.play_id,
                        'momentum_deficit': round(abs(away_deficit_start['deficit']), 2),
                        'final_momentum': round(abs(net_momentum), 2),
                        'momentum_swing': round(momentum_swing, 2),
                        'quarter': dp.quarter,
                        'start_quarter': away_deficit_start['start_quarter'],
                        'start_time': away_deficit_start['start_time'],
                        'end_time': dp.time_remaining,
                        'plays_elapsed': plays_elapsed
                    })
                # Reset after comeback is recorded or window passed
                away_deficit_start = None

        return comebacks

    def calculate_momentum_stats(
        self,
        data_points: List[MomentumDataPoint],
        home_team: str,
        away_team: str
    ) -> Dict[str, Dict]:
        """
        Calculate momentum statistics for each team including deficits and comebacks.

        Args:
            data_points: List of momentum data points
            home_team: Home team abbreviation
            away_team: Away team abbreviation

        Returns:
            Dictionary with stats for each team:
            {
                'home_team': {
                    'biggest_deficit': float,
                    'largest_comeback': float,
                    'biggest_lead': float
                },
                'away_team': {
                    'biggest_deficit': float,
                    'largest_comeback': float,
                    'biggest_lead': float
                }
            }
        """
        if not data_points:
            return {
                home_team: {'biggest_deficit': 0, 'largest_comeback': 0, 'biggest_lead': 0},
                away_team: {'biggest_deficit': 0, 'largest_comeback': 0, 'biggest_lead': 0}
            }

        home_biggest_deficit = 0.0
        home_largest_comeback = 0.0
        home_biggest_lead = 0.0
        home_worst_position = 0.0  # Track worst deficit to calculate comeback

        away_biggest_deficit = 0.0
        away_largest_comeback = 0.0
        away_biggest_lead = 0.0
        away_worst_position = 0.0

        for dp in data_points:
            net_momentum = dp.home_momentum - dp.away_momentum

            # Track HOME team stats
            if net_momentum < 0:
                # Home team is trailing
                deficit = abs(net_momentum)
                home_biggest_deficit = max(home_biggest_deficit, deficit)
                home_worst_position = min(home_worst_position, net_momentum)
            else:
                # Home team is leading
                home_biggest_lead = max(home_biggest_lead, net_momentum)
                # Calculate comeback if recovered from deficit
                if home_worst_position < 0:
                    comeback = net_momentum - home_worst_position
                    home_largest_comeback = max(home_largest_comeback, comeback)

            # Track AWAY team stats
            if net_momentum > 0:
                # Away team is trailing
                deficit = abs(net_momentum)
                away_biggest_deficit = max(away_biggest_deficit, deficit)
                away_worst_position = max(away_worst_position, net_momentum)
            else:
                # Away team is leading
                away_biggest_lead = max(away_biggest_lead, abs(net_momentum))
                # Calculate comeback if recovered from deficit
                if away_worst_position > 0:
                    comeback = abs(net_momentum - away_worst_position)
                    away_largest_comeback = max(away_largest_comeback, comeback)

        return {
            home_team: {
                'biggest_deficit': round(home_biggest_deficit, 2),
                'largest_comeback': round(home_largest_comeback, 2),
                'biggest_lead': round(home_biggest_lead, 2)
            },
            away_team: {
                'biggest_deficit': round(away_biggest_deficit, 2),
                'largest_comeback': round(away_largest_comeback, 2),
                'biggest_lead': round(away_biggest_lead, 2)
            }
        }

    def get_normalized_momentum(
        self,
        data_points: list[MomentumDataPoint]
    ) -> list[MomentumDataPoint]:
        """
        Normalize momentum values to -100 to +100 scale.
        Positive = home team momentum, Negative = away team momentum.
        """
        if not data_points:
            return []

        # Find max absolute momentum
        max_abs = max(
            max(abs(dp.home_momentum), abs(dp.away_momentum))
            for dp in data_points
        )

        if max_abs == 0:
            return data_points

        # Normalize
        normalized = []
        for dp in data_points:
            # Net momentum from home team's perspective
            net = dp.home_momentum - dp.away_momentum
            normalized_value = (net / max_abs) * 100

            normalized.append(MomentumDataPoint(
                play_id=dp.play_id,
                quarter=dp.quarter,
                time_remaining=dp.time_remaining,
                home_momentum=round(normalized_value, 2),
                away_momentum=round(-normalized_value, 2),
                momentum_delta=dp.momentum_delta,
                home_wp=dp.home_wp,
                away_wp=dp.away_wp,
                home_score=dp.home_score,
                away_score=dp.away_score,
                yardline_100=dp.yardline_100,
                down=dp.down,
                yards_to_go=dp.yards_to_go,
                event_description=dp.event_description,
                is_significant=dp.is_significant
            ))

        return normalized
