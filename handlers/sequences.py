import logging
from datetime import timedelta
from telegram import WebAppInfo, KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config import CALCULATOR_URL, MYCELIUM_APP_URL
from content.messages import (
    SEQ_A_4H, SEQ_A_DAY2, SEQ_A_DAY4, SEQ_A_DAY7,
    SEQ_B_DAY1, SEQ_B_DAY2, SEQ_B_DAY3, SEQ_B_DAY4,
    SEQ_B_DAY5, SEQ_B_DAY6, SEQ_B_DAY7,
)
from content.videos import VIDEOS
from database import get_session, User

logger = logging.getLogger(__name__)

# Sequence A: For users who didn't complete quiz
SEQUENCE_A = {
    0.17: {"video": "ever_reminder", "text": SEQ_A_4H},      # 4 hours
    2: {"video": "prisma_social_proof", "text": SEQ_A_DAY2},
    4: {"video": "phoenix_fomo", "text": SEQ_A_DAY4},
    7: {"video": "zen_gentle", "text": SEQ_A_DAY7},
}

# Sequence B: For users who completed quiz but didn't start Vision
SEQUENCE_B = {
    1: {"video": "ever_vision_preview", "text": SEQ_B_DAY1},
    2: {"video": "case_study", "text": SEQ_B_DAY2},
    3: {"video": "prisma_demo", "text": SEQ_B_DAY3},
    4: {"video": "toxic_risks", "text": SEQ_B_DAY4},
    5: {"video": "tech_demo", "text": SEQ_B_DAY5},
    6: {"video": "phoenix_marketing", "text": SEQ_B_DAY6},
    7: {"video": "ever_urgency", "text": SEQ_B_DAY7},
}


def cancel_jobs(context: ContextTypes.DEFAULT_TYPE, user_id: int, prefix: str):
    """Cancel all scheduled jobs with given prefix for user"""
    jobs = context.job_queue.jobs()
    cancelled = 0
    for job in jobs:
        if job.name and job.name.startswith(f"{prefix}_{user_id}"):
            job.schedule_removal()
            cancelled += 1
    if cancelled > 0:
        logger.info(f"Cancelled {cancelled} {prefix} jobs for user {user_id}")


def schedule_sequence_a(context: ContextTypes.DEFAULT_TYPE, user_id: int):
    """Schedule sequence A messages for a user"""
    for day, content in SEQUENCE_A.items():
        if day < 1:
            delay = timedelta(hours=int(day * 24))
        else:
            delay = timedelta(days=day)

        context.job_queue.run_once(
            send_sequence_a_message,
            when=delay,
            data={"user_id": user_id, "day": day},
            name=f"seq_a_{user_id}_{day}"
        )
    logger.info(f"Scheduled sequence A for user {user_id}")


def schedule_sequence_b(context: ContextTypes.DEFAULT_TYPE, user_id: int, score: int):
    """Schedule sequence B messages for a user"""
    for day, content in SEQUENCE_B.items():
        context.job_queue.run_once(
            send_sequence_b_message,
            when=timedelta(days=day),
            data={"user_id": user_id, "day": day, "score": score},
            name=f"seq_b_{user_id}_{day}"
        )
    logger.info(f"Scheduled sequence B for user {user_id}")


async def send_sequence_a_message(context: ContextTypes.DEFAULT_TYPE):
    """Send scheduled message for sequence A (didn't complete quiz)"""
    job = context.job
    user_id = job.data["user_id"]
    day = job.data["day"]

    db = get_session()
    try:
        # Check if user completed quiz
        db_user = db.query(User).filter(User.telegram_id == user_id).first()
        if db_user and db_user.quiz_completed:
            logger.info(f"Skipping sequence A day {day} for user {user_id} - quiz completed")
            return

        content = SEQUENCE_A.get(day)
        if not content:
            return

        keyboard = ReplyKeyboardMarkup([[
            KeyboardButton(
                "🚀 Пройти Idea Launchpad",
                web_app=WebAppInfo(url=CALCULATOR_URL)
            )
        ]], resize_keyboard=True)

        try:
            video_id = VIDEOS.get(content["video"])
            if video_id:
                await context.bot.send_video(
                    chat_id=user_id,
                    video=video_id,
                    caption=content["text"],
                    reply_markup=keyboard
                )
            else:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=content["text"],
                    reply_markup=keyboard
                )
            logger.info(f"Sent sequence A day {day} to user {user_id}")
        except Exception as e:
            logger.error(f"Failed to send sequence A message to {user_id}: {e}")
    finally:
        db.close()


async def send_sequence_b_message(context: ContextTypes.DEFAULT_TYPE):
    """Send scheduled message for sequence B (didn't start Vision)"""
    job = context.job
    user_id = job.data["user_id"]
    day = job.data["day"]
    score = job.data.get("score", 0)

    db = get_session()
    try:
        # Check if user started Vision
        db_user = db.query(User).filter(User.telegram_id == user_id).first()
        if db_user and db_user.vision_started:
            logger.info(f"Skipping sequence B day {day} for user {user_id} - Vision started")
            return

        content = SEQUENCE_B.get(day)
        if not content:
            return

        text = content["text"]
        if "{score}" in text:
            text = text.format(score=score)

        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("✨ Начать Vision Phase", url=MYCELIUM_APP_URL)
        ]])

        try:
            video_id = VIDEOS.get(content["video"])
            if video_id:
                await context.bot.send_video(
                    chat_id=user_id,
                    video=video_id,
                    caption=text,
                    reply_markup=keyboard
                )
            else:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=text,
                    reply_markup=keyboard
                )
            logger.info(f"Sent sequence B day {day} to user {user_id}")
        except Exception as e:
            logger.error(f"Failed to send sequence B message to {user_id}: {e}")
    finally:
        db.close()
