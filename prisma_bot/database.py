import logging
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import DATABASE_URL

logger = logging.getLogger(__name__)

Base = declarative_base()


class ChatLog(Base):
    """Store chat messages for context memory"""
    __tablename__ = 'chat_logs'

    id = Column(Integer, primary_key=True)
    chat_id = Column(BigInteger, index=True)
    user_id = Column(BigInteger)
    user_name = Column(String(255))
    role = Column(String(50))  # 'user' or 'assistant'
    content = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)


class BotSettings(Base):
    """Store bot settings per chat"""
    __tablename__ = 'bot_settings'

    id = Column(Integer, primary_key=True)
    chat_id = Column(BigInteger, unique=True, index=True)
    last_message_at = Column(DateTime, default=datetime.utcnow)
    last_kick_at = Column(DateTime, nullable=True)


# Database connection
engine = None
SessionLocal = None


def init_db():
    """Initialize database connection"""
    global engine, SessionLocal

    if not DATABASE_URL:
        logger.warning("DATABASE_URL not set, using SQLite fallback")
        db_url = "sqlite:///prisma_bot.db"
    else:
        db_url = DATABASE_URL

    engine = create_engine(db_url)
    SessionLocal = sessionmaker(bind=engine)

    # Create tables
    Base.metadata.create_all(engine)
    logger.info("Database initialized")


def get_session():
    """Get database session"""
    if SessionLocal is None:
        init_db()
    return SessionLocal()


def log_message(chat_id: int, user_id: int, user_name: str, role: str, content: str):
    """Log a message to the database"""
    try:
        session = get_session()
        log = ChatLog(
            chat_id=chat_id,
            user_id=user_id,
            user_name=user_name,
            role=role,
            content=content[:4000]  # Truncate if too long
        )
        session.add(log)
        session.commit()
        session.close()
    except Exception as e:
        logger.error(f"Error logging message: {e}")


def get_recent_messages(chat_id: int, limit: int = 20) -> list:
    """Get recent messages from a chat for context"""
    try:
        session = get_session()
        messages = session.query(ChatLog).filter(
            ChatLog.chat_id == chat_id
        ).order_by(ChatLog.timestamp.desc()).limit(limit).all()
        session.close()

        # Reverse to get chronological order
        return list(reversed(messages))
    except Exception as e:
        logger.error(f"Error getting messages: {e}")
        return []


def update_last_message_time(chat_id: int):
    """Update the last message timestamp for a chat"""
    try:
        session = get_session()
        settings = session.query(BotSettings).filter(
            BotSettings.chat_id == chat_id
        ).first()

        if settings:
            settings.last_message_at = datetime.utcnow()
        else:
            settings = BotSettings(chat_id=chat_id, last_message_at=datetime.utcnow())
            session.add(settings)

        session.commit()
        session.close()
    except Exception as e:
        logger.error(f"Error updating last message time: {e}")


def get_silence_duration(chat_id: int) -> float:
    """Get hours since last message in chat"""
    try:
        session = get_session()
        settings = session.query(BotSettings).filter(
            BotSettings.chat_id == chat_id
        ).first()
        session.close()

        if settings and settings.last_message_at:
            delta = datetime.utcnow() - settings.last_message_at
            return delta.total_seconds() / 3600  # Return hours
        return 0
    except Exception as e:
        logger.error(f"Error getting silence duration: {e}")
        return 0


def update_last_kick_time(chat_id: int):
    """Update when we last kicked the chat"""
    try:
        session = get_session()
        settings = session.query(BotSettings).filter(
            BotSettings.chat_id == chat_id
        ).first()

        if settings:
            settings.last_kick_at = datetime.utcnow()
            session.commit()
        session.close()
    except Exception as e:
        logger.error(f"Error updating last kick time: {e}")


def get_all_active_chats() -> list:
    """Get all chats with settings"""
    try:
        session = get_session()
        settings = session.query(BotSettings).all()
        session.close()
        return [s.chat_id for s in settings]
    except Exception as e:
        logger.error(f"Error getting active chats: {e}")
        return []
