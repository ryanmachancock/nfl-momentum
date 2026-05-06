from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base


class SharedGraph(Base):
    __tablename__ = "shared_graphs"

    id = Column(Integer, primary_key=True, index=True)
    share_code = Column(String(12), unique=True, nullable=False, index=True)
    game_id = Column(String(20), ForeignKey("games.game_id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    view_count = Column(Integer, default=0)

    # Relationship
    game = relationship("Game", back_populates="shared_graphs")

    def __repr__(self):
        return f"<SharedGraph {self.share_code} -> {self.game_id}>"
