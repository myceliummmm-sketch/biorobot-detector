import json
import logging
import traceback
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


def determine_blocker(answers) -> str:
    """Determine user's main blocker based on quiz answers.

    answers: list of 4 answer indices [q1, q2, q3, q4] where each is 0, 1, or 2

    Questions mapping (adjust based on actual quiz):
    Q1 (idea clarity): 0=clear, 1=vague, 2=none
    Q2 (experience): 0=experienced, 1=tried_failed, 2=newbie
    Q3 (priority): 0=speed, 1=balance, 2=perfect
    Q4 (time): 0=10+, 1=5-10, 2=2-5
    """
    if not answers or not isinstance(answers, list) or len(answers) < 4:
        return "Паралич старта"

    q1, q2, q3, q4 = answers[0], answers[1], answers[2], answers[3]

    # Q1: Idea clarity
    if q1 == 2:  # No idea
        return "Страх выбора"
    if q1 == 1:  # Vague idea
        return "Туманное видение"

    # Q2: Experience
    if q2 == 2:  # Newbie
        return "Синдром самозванца"
    if q2 == 1:  # Tried and failed
        return "Страх повторить провал"

    # Q3: Priority
    if q3 == 2:  # Perfect
        return "Паралич перфекционизма"
    if q3 == 1:  # Balance
        return "Паралич анализа"

    # Q4: Time
    if q4 == 2:  # 2-5 hours
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
        logger.error(f"Full traceback: {traceback.format_exc()}")
        # Send result with what we have, even if DB failed
        try:
            char_key, char_name = BLOCKER_TO_CHARACTER.get(blocker, ("ever", "Ever Green"))
            text = RESULT_WITH_BLOCKER.format(
                name=user.first_name or "друг",
                score=score,
                blocker=blocker,
                char_name=char_name
            )
            keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton("✨ Начать Vision Phase", url=MYCELIUM_APP_URL)
            ]])
            await update.message.reply_text(text=text, reply_markup=keyboard)
        except:
            # Ultimate fallback
            await update.message.reply_text(
                f"🎯 {user.first_name or 'Друг'}, спасибо за прохождение теста!\n\nНачни Vision Phase 👇",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("✨ Начать Vision Phase", url=MYCELIUM_APP_URL)
                ]])
            )
    finally:
        db.close()
