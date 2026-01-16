"""
/status command handler

Displays user's project progress from Supabase:
- Character assignment
- Blocker type
- Vision/Build/Ship progress bars
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config import TMA_VISION_URL, DESKTOP_APP_URL
from database.supabase_client import get_supabase_client
from database import get_session, User

logger = logging.getLogger(__name__)

# Character emoji mapping
CHARACTER_EMOJI = {
    "ever": "🌲",
    "prisma": "💎",
    "zen": "🧘",
    "toxic": "☢️",
    "tech_priest": "⚙️",
    "phoenix": "🔥"
}

CHARACTER_NAMES = {
    "ever": "Ever Green",
    "prisma": "Prisma",
    "zen": "Zen",
    "toxic": "Toxic",
    "tech_priest": "Tech Priest",
    "phoenix": "Phoenix"
}


def make_progress_bar(percent: int, length: int = 10) -> str:
    """Create a text-based progress bar"""
    filled = int(percent / 100 * length)
    empty = length - filled
    return "█" * filled + "░" * empty


async def status_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /status command - show user's project progress"""
    user = update.effective_user
    logger.info(f"/status from user {user.id}")

    # Try to get status from Supabase first
    supabase = get_supabase_client()

    if supabase.is_enabled:
        status = await supabase.get_project_status(user.id)

        if status:
            # Got status from Supabase
            char_key = status.get("assigned_character", "ever")
            char_emoji = CHARACTER_EMOJI.get(char_key, "🎭")
            char_name = CHARACTER_NAMES.get(char_key, "Unknown")
            blocker = status.get("quiz_blocker", "Не определён")
            vision = status.get("vision_progress", 0)
            build = status.get("build_progress", 0)
            current_phase = status.get("current_phase", "idea")

            text = f"""{char_emoji} **Syndicate Status**

🎭 Персонаж: {char_name}
🚧 Блокер: {blocker}

**Прогресс:**
💡 Idea  [{make_progress_bar(vision)}] {vision}%
🔧 Build [{make_progress_bar(build)}] {build}%
🚀 Ship  [{make_progress_bar(0)}] 0%

📍 Текущая фаза: {current_phase.upper()}"""

            # Suggest next action based on progress
            if vision == 0:
                cta_text = "🃏 Начать Vision Card"
                cta_url = TMA_VISION_URL
            elif vision < 100:
                cta_text = "🃏 Продолжить Vision Card"
                cta_url = TMA_VISION_URL
            else:
                cta_text = "💻 Перейти к Build Phase"
                cta_url = DESKTOP_APP_URL

            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton(cta_text, url=cta_url)]
            ])

            await update.message.reply_text(
                text=text,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
            return

    # Fallback: Get status from local SQLite
    try:
        db = get_session()
        db_user = db.query(User).filter(User.telegram_id == user.id).first()
        db.close()

        if db_user and db_user.quiz_completed:
            blocker = db_user.blocker or "Не определён"
            score = db_user.quiz_score or 0

            text = f"""📊 **Твой статус**

🎯 Quiz Score: {score}/100
🚧 Блокер: {blocker}

⚠️ Подключи Syndicate для полного прогресса!

Пройди Vision Phase чтобы разблокировать отслеживание."""

            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🃏 Start Vision Card", url=TMA_VISION_URL)]
            ])
        else:
            text = """📊 **Твой статус**

❌ Квиз не пройден

Пройди квиз чтобы узнать свой блокер и получить персонального проводника."""

            from config import CALCULATOR_URL
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🧮 Пройти квиз", url=CALCULATOR_URL)]
            ])

        await update.message.reply_text(
            text=text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )

    except Exception as e:
        logger.error(f"Status handler error: {e}")
        await update.message.reply_text(
            "❌ Не удалось получить статус. Попробуй позже."
        )
