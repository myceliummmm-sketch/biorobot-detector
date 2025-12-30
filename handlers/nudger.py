"""
The Nudger - Proactive messaging system

Checks user status from Supabase and sends contextual messages:
- User has character but vision_progress = 0: Encourage to start
- User has vision_progress = 100%: Toxic audit message
- User has build_progress > 0: Tech Priest continuation nudge
"""

import logging
from datetime import timedelta
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config import TMA_VISION_URL, DESKTOP_APP_URL
from database.supabase_client import get_supabase_client
from content.videos import VIDEOS

logger = logging.getLogger(__name__)

# Character-specific nudge messages
NUDGE_MESSAGES = {
    # When vision_progress = 0 (hasn't started)
    "start_vision": {
        "ever": """🌲 Ever Green:

"Твой страх понятен. {blocker} — это нормально.

Давай заземлим его. Опиши свою проблему за 30 секунд — и страх начнёт таять.

Одна карточка. Один шаг. Прямо сейчас."
""",
        "prisma": """💎 Prisma:

"Я вижу паттерн. 78% людей с твоим блокером ({blocker}) застревают на старте.

Но те, кто делает первый шаг в первые 24 часа — продвигаются в 3 раза быстрее.

Давай начнём?"
""",
        "zen": """🧘 Zen:

"Нет давления. Нет спешки.

Но твоя идея заслуживает формы. {blocker} не исчезнет сам — но станет меньше, когда ты начнёшь.

30 секунд. Одна мысль. Готов?"
""",
        "toxic": """☢️ Toxic:

"Знаю, знаю. {blocker}. Классика.

Можешь продолжать бояться. Или можешь за 30 секунд описать проблему и посмотреть, что получится.

Выбор за тобой. Я подожду... недолго."
""",
        "tech_priest": """⚙️ Tech Priest:

"Анализ показывает: {blocker} блокирует 67% твоего потенциала.

Решение: структурировать мысль в Vision Card. Время выполнения: 30 секунд.

Инициировать процесс?"
"""
    },

    # When vision_progress = 100% (completed vision)
    "vision_complete": """☢️ Toxic:

"Красивое видение. Правда.

Но пока это только слова. Я нашёл 3 дыры в твоём плане.

Иди на десктоп — Tech Priest подготовил аудит. Посмотрим, выдержит ли твоя идея проверку реальностью."
""",

    # When build_progress > 0 (started building)
    "continue_build": """⚙️ Tech Priest:

"Код ждёт. Прогресс: {build_progress}%.

Система готова к следующей итерации. Каждый день простоя — потерянный импульс.

Продолжим?"
""",

    # Social proof pulse
    "syndicate_pulse": """💎 Prisma:

"Syndicate активен:
{activities}

{active_today} человек работают над проектами прямо сейчас.

Присоединяйся?"
"""
}


async def check_and_nudge_user(
    context: ContextTypes.DEFAULT_TYPE,
    telegram_id: int,
    chat_id: int
):
    """
    Check user status and send appropriate nudge message

    Called from:
    - Scheduled job (daily check)
    - After user completes certain actions
    """
    supabase = get_supabase_client()

    if not supabase.is_enabled:
        logger.debug("Supabase not enabled, skipping nudge")
        return

    try:
        status = await supabase.get_project_status(telegram_id)

        if not status:
            logger.debug(f"No status for user {telegram_id}")
            return

        char_key = status.get("assigned_character")
        blocker = status.get("quiz_blocker", "страх")
        vision_progress = status.get("vision_progress", 0)
        build_progress = status.get("build_progress", 0)

        # No character assigned = hasn't completed quiz
        if not char_key:
            logger.debug(f"User {telegram_id} has no character, skip nudge")
            return

        # CASE 1: Vision not started
        if vision_progress == 0:
            templates = NUDGE_MESSAGES["start_vision"]
            message = templates.get(char_key, templates["ever"]).format(blocker=blocker)

            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🃏 Start Vision Card", url=TMA_VISION_URL)]
            ])

            # Try to send character video
            video_key = f"{char_key}_nudge"
            video_id = VIDEOS.get(video_key)

            if video_id:
                await context.bot.send_video(
                    chat_id=chat_id,
                    video=video_id,
                    caption=message,
                    reply_markup=keyboard
                )
            else:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=message,
                    reply_markup=keyboard
                )

            logger.info(f"Sent start_vision nudge to {telegram_id}")
            return

        # CASE 2: Vision complete (100%)
        if vision_progress >= 100 and build_progress == 0:
            message = NUDGE_MESSAGES["vision_complete"]

            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("💻 See Audit on Desktop", url=DESKTOP_APP_URL)]
            ])

            # Toxic video for audit reveal
            video_id = VIDEOS.get("toxic_audit")

            if video_id:
                await context.bot.send_video(
                    chat_id=chat_id,
                    video=video_id,
                    caption=message,
                    reply_markup=keyboard
                )
            else:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=message,
                    reply_markup=keyboard
                )

            logger.info(f"Sent vision_complete nudge to {telegram_id}")
            return

        # CASE 3: Building in progress
        if build_progress > 0 and build_progress < 100:
            message = NUDGE_MESSAGES["continue_build"].format(build_progress=build_progress)

            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("💻 Continue Building", url=DESKTOP_APP_URL)]
            ])

            await context.bot.send_message(
                chat_id=chat_id,
                text=message,
                reply_markup=keyboard
            )

            logger.info(f"Sent continue_build nudge to {telegram_id}")
            return

        logger.debug(f"No nudge condition met for user {telegram_id}")

    except Exception as e:
        logger.error(f"Nudge error for {telegram_id}: {e}")


async def schedule_nudge_check(context: ContextTypes.DEFAULT_TYPE, telegram_id: int, chat_id: int, delay_hours: int = 24):
    """Schedule a nudge check for later"""
    job_name = f"nudge_{telegram_id}"

    # Remove existing nudge job if any
    current_jobs = context.job_queue.get_jobs_by_name(job_name)
    for job in current_jobs:
        job.schedule_removal()

    # Schedule new nudge
    context.job_queue.run_once(
        callback=lambda ctx: check_and_nudge_user(ctx, telegram_id, chat_id),
        when=timedelta(hours=delay_hours),
        name=job_name,
        data={"telegram_id": telegram_id, "chat_id": chat_id}
    )

    logger.info(f"Scheduled nudge for {telegram_id} in {delay_hours}h")


async def send_syndicate_pulse(context: ContextTypes.DEFAULT_TYPE, chat_id: int):
    """Send social proof message with recent syndicate activity"""
    supabase = get_supabase_client()

    if not supabase.is_enabled:
        return

    try:
        pulse = await supabase.get_syndicate_pulse(limit=3)

        if not pulse:
            return

        activities = pulse.get("activities", [])
        active_today = pulse.get("active_today", 0)

        if not activities:
            return

        # Format activities
        activity_lines = []
        for act in activities[:3]:
            user = act.get("user", "Someone")
            action = act.get("action", "did something")
            time_ago = act.get("time_ago", "recently")
            activity_lines.append(f"• {user} {action} ({time_ago})")

        activities_text = "\n".join(activity_lines)

        message = NUDGE_MESSAGES["syndicate_pulse"].format(
            activities=activities_text,
            active_today=active_today
        )

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🃏 Join the Action", url=TMA_VISION_URL)]
        ])

        await context.bot.send_message(
            chat_id=chat_id,
            text=message,
            reply_markup=keyboard
        )

        logger.info(f"Sent syndicate pulse to {chat_id}")

    except Exception as e:
        logger.error(f"Syndicate pulse error: {e}")
