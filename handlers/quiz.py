import json
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config import MYCELIUM_APP_URL
from content.messages import RESULT_HIGH_SCORE, RESULT_WITH_BLOCKER
from content.videos import VIDEOS
from database import get_session, User
from .sequences import cancel_jobs, schedule_sequence_b

logger = logging.getLogger(__name__)

# Blockers mapping to characters
BLOCKER_TO_CHARACTER = {
    "Страх выбора": ("prisma", "Prisma"),
    "Туманное видение": ("ever", "Ever Green"),
    "Синдром самозванца": ("zen", "Zen"),
    "Страх повторить провал": ("toxic", "Toxic"),
    "Паралич перфекционизма": ("tech_priest", "Tech Priest"),
    "Паралич анализа": ("prisma", "Prisma"),
    "Нехватка времени": ("zen", "Zen"),
    "Паралич старта": ("ever", "Ever Green"),
}


def determine_blocker(answers: dict) -> str:
    """Determine user's main blocker based on quiz answers"""
    idea = answers.get('idea', '')
    experience = answers.get('experience', '')
    priority = answers.get('priority', '')
    time_ans = answers.get('time', '')

    if idea == 'none':
        return "Страх выбора"
    if idea == 'vague':
        return "Туманное видение"
    if experience == 'newbie':
        return "Синдром самозванца"
    if experience == 'tried':
        return "Страх повторить провал"
    if priority == 'perfect':
        return "Паралич перфекционизма"
    if priority == 'balance':
        return "Паралич анализа"
    if time_ans == '2-5':
        return "Нехватка времени"
    return "Паралич старта"


async def quiz_result_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process quiz results from Mini App"""
    user = update.effective_user
    logger.info(f"Quiz result handler triggered for user {user.id}")

    # Parse data from WebApp
    try:
        raw_data = update.effective_message.web_app_data.data
        logger.info(f"Raw WebApp data: {raw_data}")
        data = json.loads(raw_data)
        logger.info(f"Parsed quiz data from user {user.id}: {data}")
    except Exception as e:
        logger.error(f"Failed to parse web app data: {e}")
        # Send fallback message even on parse error
        await update.message.reply_text(
            "🎯 Спасибо за прохождение теста!\n\nНачни Vision Phase — это бесплатно 👇",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("✨ Начать Vision Phase", url=MYCELIUM_APP_URL)
            ]])
        )
        return

    # Extract score - handle different data formats
    score = data.get('score', data.get('result', data.get('total', 50)))
    answers = data.get('answers', data.get('responses', {}))
    blocker = determine_blocker(answers)

    logger.info(f"Processed: score={score}, blocker={blocker}")

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
            logger.info(f"Created new user {user.id} in quiz handler")

        db_user.quiz_completed = True
        db_user.quiz_score = score
        db_user.blocker = blocker
        db.commit()
        logger.info(f"User {user.id} completed quiz: score={score}, blocker={blocker}")

        # Cancel sequence A jobs
        cancel_jobs(context, user.id, "seq_a")

        # Send personalized result
        char_key, char_name = BLOCKER_TO_CHARACTER.get(blocker, ("ever", "Ever Green"))

        if score >= 80:
            text = RESULT_HIGH_SCORE.format(name=user.first_name or "друг", score=score)
            video_key = "phoenix_success"
        else:
            text = RESULT_WITH_BLOCKER.format(
                name=user.first_name or "друг",
                score=score,
                blocker=blocker,
                char_name=char_name
            )
            video_key = f"{char_key}_blocker"

        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("✨ Начать Vision Phase", url=MYCELIUM_APP_URL)
        ]])

        video_id = VIDEOS.get(video_key)
        if video_id:
            await update.message.reply_video(
                video=video_id,
                caption=text,
                reply_markup=keyboard
            )
        else:
            await update.message.reply_text(text=text, reply_markup=keyboard)

        logger.info(f"Sent quiz result to user {user.id}")

        # Schedule sequence B
        schedule_sequence_b(context, user.id, score)

    except Exception as e:
        logger.error(f"Error in quiz handler: {e}")
        # Fallback response on any error
        await update.message.reply_text(
            f"🎯 {user.first_name or 'Друг'}, спасибо за прохождение теста!\n\nТвой результат обработан. Начни Vision Phase 👇",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("✨ Начать Vision Phase", url=MYCELIUM_APP_URL)
            ]])
        )
    finally:
        db.close()
