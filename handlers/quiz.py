import json
import logging
import traceback
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config import MYCELIUM_APP_URL, TMA_VISION_URL, DESKTOP_APP_URL
from content.messages import RESULT_HIGH_SCORE, RESULT_WITH_BLOCKER
from content.videos import VIDEOS
from database import get_session, User
from database.supabase_client import get_supabase_client
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
    """Determine user's main blocker based on quiz answers."""
    if not answers or not isinstance(answers, list) or len(answers) < 4:
        return "Паралич старта"

    q1, q2, q3, q4 = answers[0], answers[1], answers[2], answers[3]

    if q1 == 2:
        return "Страх выбора"
    if q1 == 1:
        return "Туманное видение"
    if q2 == 2:
        return "Синдром самозванца"
    if q2 == 1:
        return "Страх повторить провал"
    if q3 == 2:
        return "Паралич перфекционизма"
    if q3 == 1:
        return "Паралич анализа"
    if q4 == 2:
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
        await update.message.reply_text(
            "🎯 Спасибо за прохождение теста!\n\nНачни Vision Phase — это бесплатно 👇",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("✨ Начать Vision Phase", url=MYCELIUM_APP_URL)
            ]])
        )
        return

    # Extract score and determine blocker
    score = data.get('score', data.get('result', data.get('total', 50)))
    answers = data.get('answers', data.get('responses', []))
    blocker = determine_blocker(answers)
    char_key, char_name = BLOCKER_TO_CHARACTER.get(blocker, ("ever", "Ever Green"))

    logger.info(f"Processed: score={score}, blocker={blocker}, char_key={char_key}")

    # Prepare message
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

    # FIRST: Send video/message (before DB operations!)
    video_id = VIDEOS.get(video_key)
    logger.info(f"Looking for video: key={video_key}, video_id={video_id[:30] if video_id else None}...")

    if video_id:
        try:
            await update.message.reply_video(
                video=video_id,
                caption=text,
                reply_markup=keyboard
            )
            logger.info(f"Video sent successfully: {video_key}")
        except Exception as video_err:
            logger.error(f"Failed to send video {video_key}: {video_err}")
            await update.message.reply_text(text=text, reply_markup=keyboard)
    else:
        logger.warning(f"No video found for key: {video_key}")
        await update.message.reply_text(text=text, reply_markup=keyboard)

    # THEN: Database operations (separate try block)
    try:
        db = get_session()
        db_user = db.query(User).filter(User.telegram_id == user.id).first()
        if not db_user:
            db_user = User(
                telegram_id=user.id,
                username=user.username,
                first_name=user.first_name
            )
            db.add(db_user)

        db_user.quiz_completed = True
        db_user.quiz_score = score
        db_user.blocker = blocker
        db.commit()
        db.close()
        logger.info(f"User {user.id} saved to DB: score={score}, blocker={blocker}")

        # Cancel sequence A and schedule B
        cancel_jobs(context, user.id, "seq_a")
        schedule_sequence_b(context, user.id, score)

    except Exception as db_err:
        logger.error(f"DB error (video already sent): {db_err}")

    # SYNC TO SUPABASE: Send quiz results to the Syndicate
    try:
        supabase = get_supabase_client()
        if supabase.is_enabled:
            await supabase.sync_user_status(
                telegram_id=user.id,
                username=user.username,
                first_name=user.first_name,
                quiz_blocker=blocker,
                assigned_character=char_key,
                quiz_score=score,
                onboarding_step="quiz_complete"
            )
            logger.info(f"User {user.id} synced to Supabase: blocker={blocker}, char={char_key}")

            # Send follow-up message with Identity Card CTA
            follow_up = f"""🎭 Твой Identity Card готов в Синдикате.

{char_name} теперь твой проводник. Страх "{blocker}" — это не приговор, а точка роста.

Давай превратим видение в актив. Опиши свою идею за 30 секунд 👇"""

            vision_keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🃏 Start Vision Card", url=TMA_VISION_URL)],
                [InlineKeyboardButton("💻 Open Desktop App", url=DESKTOP_APP_URL)]
            ])

            await update.message.reply_text(text=follow_up, reply_markup=vision_keyboard)

            # Send community invite
            community_msg = """🌐 Присоединяйся к Syndicate Builders!

Делимся опытом, разбираем кейсы и разыгрываем призы за лучшие проекты.

Здесь строят вместе 👇"""

            community_keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🚀 Войти в комьюнити", url="https://t.me/mDAOsists")]
            ])

            await update.message.reply_text(text=community_msg, reply_markup=community_keyboard)

    except Exception as sync_err:
        logger.error(f"Supabase sync error: {sync_err}")
