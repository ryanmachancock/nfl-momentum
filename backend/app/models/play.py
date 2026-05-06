from sqlalchemy import Column, Integer, String, Boolean, Float, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from ..database import Base


class Play(Base):
    __tablename__ = "plays"

    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(String(20), ForeignKey("games.game_id"), nullable=False, index=True)
    play_id = Column(Integer, nullable=False)

    # Game state
    quarter = Column(Integer)
    time_remaining = Column(String(10))  # "12:34"
    down = Column(Integer)
    yards_to_go = Column(Integer)
    yard_line = Column(Integer)  # yards from opponent's end zone

    # Teams
    posteam = Column(String(5))  # Possession team
    defteam = Column(String(5))  # Defensive team

    # Score tracking
    home_score = Column(Integer, default=0)  # Home team score at time of play
    away_score = Column(Integer, default=0)  # Away team score at time of play
    score_differential = Column(Integer, default=0)  # Home score - Away score

    # Field position and game context
    yardline_100 = Column(Integer)  # Yards from opponent's end zone (0-100)
    goal_to_go = Column(Boolean, default=False)
    drive_number = Column(Integer)

    # Expected Points (from nflfastR)
    ep = Column(Float)  # Expected points before play
    epa = Column(Float)  # Expected points added by play

    # Play info
    play_type = Column(String(20))
    yards_gained = Column(Integer)
    description = Column(String(500))

    # Event flags
    touchdown = Column(Boolean, default=False)
    pass_touchdown = Column(Boolean, default=False)
    rush_touchdown = Column(Boolean, default=False)
    return_touchdown = Column(Boolean, default=False)
    interception = Column(Boolean, default=False)
    fumble_lost = Column(Boolean, default=False)
    sack = Column(Boolean, default=False)
    safety = Column(Boolean, default=False)
    penalty = Column(Boolean, default=False)
    penalty_yards = Column(Integer)
    first_down = Column(Boolean, default=False)
    third_down_converted = Column(Boolean, default=False)
    third_down_failed = Column(Boolean, default=False)
    fourth_down_converted = Column(Boolean, default=False)
    fourth_down_failed = Column(Boolean, default=False)
    field_goal_result = Column(String(10))  # made, missed, blocked
    tackled_for_loss = Column(Boolean, default=False)

    # Player names for key events
    passer_player_name = Column(String(50))
    rusher_player_name = Column(String(50))
    receiver_player_name = Column(String(50))
    interception_player_name = Column(String(50))
    sack_player_name = Column(String(50))
    fumbled_player_name = Column(String(50))
    fumble_recovery_player_name = Column(String(50))
    td_player_name = Column(String(50))
    kicker_player_name = Column(String(50))
    safety_player_name = Column(String(50))
    punt_returner_player_name = Column(String(50))
    kickoff_returner_player_name = Column(String(50))

    # Win probability (from nflfastR)
    home_wp = Column(Float)  # Home team win probability (0-1)
    away_wp = Column(Float)  # Away team win probability (0-1)

    # Calculated momentum values
    home_momentum = Column(Float, default=0.0)
    away_momentum = Column(Float, default=0.0)
    momentum_delta = Column(Float, default=0.0)

    # Relationship
    game = relationship("Game", back_populates="plays")

    __table_args__ = (
        UniqueConstraint("game_id", "play_id", name="uq_game_play"),
    )

    def __repr__(self):
        return f"<Play {self.game_id}:{self.play_id} Q{self.quarter}>"
