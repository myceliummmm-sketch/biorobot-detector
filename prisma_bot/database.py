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
    is_muted = Column(Integer, default=0)  # 0 = active, 1 = muted


class PermanentMemory(Base):
    """Store permanent memory entries that persist across conversations"""
    __tablename__ = 'permanent_memory'

    id = Column(Integer, primary_key=True)
    chat_id = Column(BigInteger, index=True)
    category = Column(String(100))  # decision, task, insight, fact, etc.
    content = Column(Text)
    added_by = Column(String(255))  # user who added or "prisma" if auto
    timestamp = Column(DateTime, default=datetime.utcnow)


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


def get_today_messages(chat_id: int) -> list:
    """Get all messages from today for daily summary"""
    try:
        session = get_session()
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

        messages = session.query(ChatLog).filter(
            ChatLog.chat_id == chat_id,
            ChatLog.timestamp >= today_start
        ).order_by(ChatLog.timestamp.asc()).all()
        session.close()

        return messages
    except Exception as e:
        logger.error(f"Error getting today messages: {e}")
        return []


# === PERMANENT MEMORY FUNCTIONS ===

def add_memory(chat_id: int, category: str, content: str, added_by: str = "prisma") -> bool:
    """Add a permanent memory entry"""
    try:
        session = get_session()
        memory = PermanentMemory(
            chat_id=chat_id,
            category=category,
            content=content[:2000],  # Limit size
            added_by=added_by
        )
        session.add(memory)
        session.commit()
        session.close()
        logger.info(f"Added memory [{category}]: {content[:50]}...")
        return True
    except Exception as e:
        logger.error(f"Error adding memory: {e}")
        return False


def get_all_memories(chat_id: int) -> list:
    """Get all permanent memories for a chat"""
    try:
        session = get_session()
        memories = session.query(PermanentMemory).filter(
            PermanentMemory.chat_id == chat_id
        ).order_by(PermanentMemory.timestamp.desc()).all()
        session.close()
        return memories
    except Exception as e:
        logger.error(f"Error getting memories: {e}")
        return []


def get_memories_by_category(chat_id: int, category: str) -> list:
    """Get memories by category"""
    try:
        session = get_session()
        memories = session.query(PermanentMemory).filter(
            PermanentMemory.chat_id == chat_id,
            PermanentMemory.category == category
        ).order_by(PermanentMemory.timestamp.desc()).all()
        session.close()
        return memories
    except Exception as e:
        logger.error(f"Error getting memories by category: {e}")
        return []


def delete_memory(memory_id: int) -> bool:
    """Delete a memory by ID"""
    try:
        session = get_session()
        memory = session.query(PermanentMemory).filter(
            PermanentMemory.id == memory_id
        ).first()
        if memory:
            session.delete(memory)
            session.commit()
        session.close()
        return True
    except Exception as e:
        logger.error(f"Error deleting memory: {e}")
        return False


def get_memory_context(chat_id: int, limit: int = 20) -> str:
    """Get formatted memory context for prompts"""
    try:
        memories = get_all_memories(chat_id)[:limit]
        if not memories:
            return ""

        lines = ["=== ПОСТОЯННАЯ ПАМЯТЬ ==="]
        for m in memories:
            lines.append(f"[{m.category}] {m.content}")

        return "\n".join(lines)
    except Exception as e:
        logger.error(f"Error getting memory context: {e}")
        return ""


# === MUTE FUNCTIONS ===

def is_chat_muted(chat_id: int) -> bool:
    """Check if chat is muted"""
    try:
        session = get_session()
        settings = session.query(BotSettings).filter(
            BotSettings.chat_id == chat_id
        ).first()
        session.close()
        return settings.is_muted == 1 if settings else False
    except Exception as e:
        logger.error(f"Error checking mute status: {e}")
        return False


def set_chat_muted(chat_id: int, muted: bool) -> bool:
    """Set chat mute status"""
    try:
        session = get_session()
        settings = session.query(BotSettings).filter(
            BotSettings.chat_id == chat_id
        ).first()

        if settings:
            settings.is_muted = 1 if muted else 0
        else:
            settings = BotSettings(chat_id=chat_id, is_muted=1 if muted else 0)
            session.add(settings)

        session.commit()
        session.close()
        logger.info(f"Chat {chat_id} mute status: {muted}")
        return True
    except Exception as e:
        logger.error(f"Error setting mute status: {e}")
        return False
