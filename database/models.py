from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, index=True)
    username = Column(String, nullable=True)
    first_name = Column(String, nullable=True)

    # Quiz state
    quiz_completed = Column(Boolean, default=False)
    quiz_score = Column(Integer, nullable=True)
    blocker = Column(String, nullable=True)

    # Vision state
    vision_started = Column(Boolean, default=False)

    # Tracking
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow)

    # Sequence tracking
    sequence_a_day = Column(Integer, default=0)  # Last sent day in sequence A
    sequence_b_day = Column(Integer, default=0)  # Last sent day in sequence B

    def __repr__(self):
        return f"<User {self.telegram_id}: {self.first_name}>"
