import logging
from datetime import datetime
from telegram import Update, WebAppInfo, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ContextTypes

from config import CALCULATOR_URL
from content.messages import WELCOME_MESSAGE
from content.videos import VIDEOS
from database import get_session, User
from .sequences import schedule_sequence_a

logger = logging.getLogger(__name__)


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Welcome message with calculator button"""
    user = update.effective_user
    db = get_session()

    try:
        # Get or create user in DB
        db_user = db.query(User).filter(User.telegram_id == user.id).first()
        if not db_user:
            db_user = User(
                telegram_id=user.id,
                username=user.username,
                first_name=user.first_name
            )
            db.add(db_user)
            db.commit()
            logger.info(f"New user created: {user.id} ({user.first_name})")

        # Update last active
        db_user.last_active = datetime.utcnow()
        db.commit()

        # Send welcome
        text = WELCOME_MESSAGE.format(name=user.first_name or "друг")
        keyboard = ReplyKeyboardMarkup([[
            KeyboardButton(
                "🚀 Пройти Idea Launchpad",
                web_app=WebAppInfo(url=CALCULATOR_URL)
            )
        ]], resize_keyboard=True)

        video_id = VIDEOS.get("ever_welcome")
        if video_id:
            await update.message.reply_video(
                video=video_id,
                caption=text,
                reply_markup=keyboard
            )
        else:
            await update.message.reply_text(text=text, reply_markup=keyboard)

        # Schedule sequence A (if they don't complete quiz)
        schedule_sequence_a(context, user.id)

        logger.info(f"Start handler completed for user {user.id}")

    finally:
        db.close()
