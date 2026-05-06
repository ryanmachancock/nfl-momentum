from sqlalchemy import Column, Integer, String, Date, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base


class Game(Base):
    __tablename__ = "games"

    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(String(20), unique=True, nullable=False, index=True)
    season = Column(Integer, nullable=False, index=True)
    week = Column(Integer, nullable=False, index=True)
    game_type = Column(String(10))  # REG, WC, DIV, CON, SB
    home_team = Column(String(5), nullable=False)
    away_team = Column(String(5), nullable=False)
    home_score = Column(Integer)
    away_score = Column(Integer)
    game_date = Column(Date)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    plays = relationship("Play", back_populates="game", cascade="all, delete-orphan")
    shared_graphs = relationship("SharedGraph", back_populates="game")

    def __repr__(self):
        return f"<Game {self.game_id}: {self.away_team} @ {self.home_team}>"
