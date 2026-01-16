"""
Simple SQLite database for storing active chats
Auto-remembers chats where Kuzya has talked
"""

import sqlite3
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# Database file path
DB_PATH = Path(__file__).parent / "kuzya.db"


def get_connection():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize database tables"""
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS active_chats (
                chat_id INTEGER PRIMARY KEY,
                chat_title TEXT,
                first_seen_at TEXT,
                last_message_at TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER,
                user_name TEXT,
                role TEXT,
                content TEXT,
                timestamp TEXT
            )
        """)

        cursor.execute("CREATE INDEX IF NOT EXISTS idx_chat_logs_chat_id ON chat_logs(chat_id)")

        conn.commit()
        conn.close()
        logger.info("Database initialized")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")


def register_chat(chat_id: int, chat_title: str = None):
    """Register a chat (or update last message time)"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        now = datetime.utcnow().isoformat()

        # Check if exists
        cursor.execute("SELECT chat_id FROM active_chats WHERE chat_id = ?", (chat_id,))
        exists = cursor.fetchone()

        if exists:
            cursor.execute(
                "UPDATE active_chats SET last_message_at = ?, chat_title = COALESCE(?, chat_title) WHERE chat_id = ?",
                (now, chat_title, chat_id)
            )
        else:
            cursor.execute(
                "INSERT INTO active_chats (chat_id, chat_title, first_seen_at, last_message_at) VALUES (?, ?, ?, ?)",
                (chat_id, chat_title, now, now)
            )
            logger.info(f"New chat registered: {chat_id} ({chat_title})")

        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Error registering chat: {e}")


def get_all_active_chats() -> list:
    """Get all registered chat IDs"""
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT chat_id FROM active_chats")
        rows = cursor.fetchall()
        conn.close()

        return [row["chat_id"] for row in rows]
    except Exception as e:
        logger.error(f"Error getting active chats: {e}")
        return []


def remove_chat(chat_id: int):
    """Remove a chat (e.g., if bot was kicked)"""
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM active_chats WHERE chat_id = ?", (chat_id,))

        conn.commit()
        conn.close()
        logger.info(f"Chat removed: {chat_id}")
    except Exception as e:
        logger.error(f"Error removing chat: {e}")


def log_message(chat_id: int, user_name: str, role: str, content: str):
    """Log a message to the database"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        now = datetime.utcnow().isoformat()

        cursor.execute(
            "INSERT INTO chat_logs (chat_id, user_name, role, content, timestamp) VALUES (?, ?, ?, ?, ?)",
            (chat_id, user_name, role, content[:2000], now)
        )

        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Error logging message: {e}")


def get_recent_messages(chat_id: int, limit: int = 20) -> list:
    """Get recent messages from a chat for context"""
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT user_name, role, content FROM chat_logs WHERE chat_id = ? ORDER BY id DESC LIMIT ?",
            (chat_id, limit)
        )
        rows = cursor.fetchall()
        conn.close()

        # Reverse to get chronological order
        return list(reversed([dict(row) for row in rows]))
    except Exception as e:
        logger.error(f"Error getting messages: {e}")
        return []


# Initialize on import
init_db()
