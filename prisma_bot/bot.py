import logging
import random
import asyncio
from datetime import datetime, time
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

try:
    import pytz
    PYTZ_AVAILABLE = True
except ImportError:
    PYTZ_AVAILABLE = False

from config import (
    PRISMA_BOT_TOKEN,
    BOT_NAME,
    BOT_NAMES,
    TRIGGER_KEYWORDS,
    SILENCE_KICK_HOURS,
    SILENCE_ALARM_HOURS,
    RANDOM_INSIGHT_CHANCE,
    PROACTIVE_CHECK_MINUTES,
    TIMEZONE,
    DAILY_CHECKINS,
    CHECKIN_PROMPTS,
    GOOGLE_DOCS_FOLDER_ID,
    ADMIN_USERNAME
)
from database import (
    init_db,
    log_message,
    update_last_message_time,
    get_silence_duration,
    update_last_kick_time,
    get_all_active_chats,
    get_today_messages
)
from gemini_client import get_prisma_client
from google_docs_client import get_docs_client
from github_client import get_github_client

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all incoming messages - log and maybe respond"""
    message = update.message
    if not message or not message.text:
        return

    chat_id = message.chat_id
    user = message.from_user

    # Skip bots
    if user.is_bot:
        return

    user_name = user.first_name or user.username or "аноним"

    # Log message to DB
    log_message(chat_id, user.id, user_name, "user", message.text)
    update_last_message_time(chat_id)

    logger.info(f"Message from {user_name}: {message.text[:50]}...")

    # Check if bot should respond
    bot_username = (await context.bot.get_me()).username
    text_lower = message.text.lower()

    is_reply_to_bot = (
        message.reply_to_message and
        message.reply_to_message.from_user and
        message.reply_to_message.from_user.id == context.bot.id
    )
    is_mention = f"@{bot_username}" in message.text if bot_username else False
    is_called = any(name in text_lower for name in BOT_NAMES)
    has_keyword = any(keyword in text_lower for keyword in TRIGGER_KEYWORDS)

    # Always respond to direct calls, mentions, replies
    # 30% chance to respond to keywords
    if is_reply_to_bot or is_mention or is_called:
        pass  # Respond
    elif has_keyword and random.random() < 0.3:
        pass  # 30% chance on keywords
    else:
        return

    logger.info(f"Responding to {user_name}")

    # Show typing
    await context.bot.send_chat_action(chat_id=chat_id, action="typing")
    await asyncio.sleep(random.uniform(1.0, 2.0))

    try:
        prisma = get_prisma_client()
        response = await prisma.generate_response(chat_id, user_name, message.text)

        # Log bot response
        log_message(chat_id, 0, "Prisma", "assistant", response)

        await message.reply_text(response)
        logger.info(f"Sent response: {response[:50]}...")

    except Exception as e:
        logger.error(f"Error: {e}")


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle photos"""
    message = update.message
    if not message or not message.photo:
        return

    chat_id = message.chat_id
    user = message.from_user

    if user.is_bot:
        return

    user_name = user.first_name or user.username or "аноним"
    caption = message.caption or ""

    # Log
    log_message(chat_id, user.id, user_name, "user", f"[ФОТО] {caption}")
    update_last_message_time(chat_id)

    # Check if should respond
    bot_username = (await context.bot.get_me()).username
    caption_lower = caption.lower()

    is_reply_to_bot = (
        message.reply_to_message and
        message.reply_to_message.from_user and
        message.reply_to_message.from_user.id == context.bot.id
    )
    is_mention = f"@{bot_username}" in caption if bot_username else False
    is_called = any(name in caption_lower for name in BOT_NAMES)

    if not (is_reply_to_bot or is_mention or is_called):
        return

    logger.info(f"Processing photo from {user_name}")

    await context.bot.send_chat_action(chat_id=chat_id, action="typing")

    try:
        photo = message.photo[-1]
        file = await context.bot.get_file(photo.file_id)
        photo_bytes = await file.download_as_bytearray()

        prisma = get_prisma_client()
        response = await prisma.generate_response_with_image(
            chat_id, user_name, caption or "что думаешь?", bytes(photo_bytes)
        )

        log_message(chat_id, 0, "Prisma", "assistant", response)
        await message.reply_text(response)

    except Exception as e:
        logger.error(f"Error processing photo: {e}")


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start"""
    await update.message.reply_text(
        "○ привет! я prisma — ai операционщица mycelium.\n\n"
        "помогаю с прогрессом и держу фокус. тегни когда нужен совет ▸"
    )


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /status"""
    chat_id = update.message.chat_id
    silence = get_silence_duration(chat_id)

    status = "активен ✨" if silence < SILENCE_KICK_HOURS else "притих 💤" if silence < SILENCE_ALARM_HOURS else "тихо ⚡"

    # Get GitHub status
    github = get_github_client()
    github_status = ""
    if github.is_available():
        commits = github.get_today_commits()
        github_status = f"\n● GitHub: {len(commits)} коммитов сегодня"

    await update.message.reply_text(
        f"▸ статус: {status}\n"
        f"○ тишина: {silence:.1f}ч{github_status}"
    )


async def prompt_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /prompt - only for admin"""
    user = update.message.from_user
    username = user.username or ""

    # Check if user is admin
    if username.lower() != ADMIN_USERNAME.lower():
        await update.message.reply_text("○ эта команда только для Артема")
        return

    # Get the prompt text
    if not context.args:
        await update.message.reply_text(
            "▸ использование:\n"
            "/prompt добавить [текст] — добавить в промпт\n"
            "/prompt показать — показать текущие дополнения"
        )
        return

    action = context.args[0].lower()
    text = " ".join(context.args[1:]) if len(context.args) > 1 else ""

    if action == "показать":
        # TODO: read from DB
        await update.message.reply_text("○ дополнений к промпту пока нет")
    elif action == "добавить" and text:
        # TODO: save to DB
        await update.message.reply_text(f"● добавлено в промпт:\n{text}")
        logger.info(f"Admin {username} added to prompt: {text}")
    else:
        await update.message.reply_text("○ не понял команду. /prompt для справки")


async def proactive_check(context: ContextTypes.DEFAULT_TYPE):
    """Proactive check - kick silent chats"""

    # Night mode: don't send messages between 23:00 and 9:00 (Spain time)
    if PYTZ_AVAILABLE:
        tz = pytz.timezone(TIMEZONE)
        current_hour = datetime.now(tz).hour
        if current_hour >= 23 or current_hour < 9:
            logger.info("Night mode: skipping proactive check")
            return

    logger.info("Running proactive check...")

    chats = get_all_active_chats()

    for chat_id in chats:
        try:
            silence = get_silence_duration(chat_id)

            kick_type = None

            if silence >= SILENCE_ALARM_HOURS:
                kick_type = "alarm"
            elif silence >= SILENCE_KICK_HOURS:
                kick_type = "gentle"
            elif random.random() < RANDOM_INSIGHT_CHANCE:
                kick_type = "insight"

            if kick_type:
                logger.info(f"Kicking chat {chat_id} with {kick_type}")

                prisma = get_prisma_client()
                message = await prisma.generate_kick_message(chat_id, kick_type)

                await context.bot.send_message(chat_id=chat_id, text=message)
                log_message(chat_id, 0, "Prisma", "assistant", message)
                update_last_kick_time(chat_id)

        except Exception as e:
            logger.error(f"Error kicking chat {chat_id}: {e}")


async def daily_checkin(context: ContextTypes.DEFAULT_TYPE):
    """Send daily check-in message to all active chats"""
    checkin_type = context.job.data.get("type", "afternoon")
    logger.info(f"Running daily {checkin_type} check-in...")

    chats = get_all_active_chats()

    if not chats:
        logger.info("No active chats for check-in")
        return

    # Get GitHub update
    github_update = ""
    github = get_github_client()
    if github.is_available():
        github_summary = github.get_summary()
        if github_summary:
            github_update = f"\n\nGITHUB_UPDATE:\n{github_summary}"

    # Get Google Docs update if available
    docs_update = ""
    if GOOGLE_DOCS_FOLDER_ID:
        docs_client = get_docs_client()
        if docs_client.is_available():
            docs_update = docs_client.get_recent_updates(GOOGLE_DOCS_FOLDER_ID)
            if docs_update:
                docs_update = f"\n\nDOCS_UPDATE:\n{docs_update}"

    for chat_id in chats:
        try:
            prisma = get_prisma_client()

            # Get checkin prompt
            prompt = CHECKIN_PROMPTS.get(checkin_type, CHECKIN_PROMPTS["afternoon"])

            # Add updates to prompt
            prompt += github_update + docs_update

            message = await prisma.generate_checkin_message(chat_id, checkin_type, prompt)

            await context.bot.send_message(chat_id=chat_id, text=message)
            log_message(chat_id, 0, "Prisma", "assistant", f"[{checkin_type.upper()}] {message}")

            logger.info(f"Sent {checkin_type} check-in to chat {chat_id}")

        except Exception as e:
            logger.error(f"Error sending check-in to {chat_id}: {e}")


def main():
    """Start Prisma bot"""
    if not PRISMA_BOT_TOKEN:
        raise ValueError("PRISMA_BOT_TOKEN is required")

    # Initialize database
    init_db()

    logger.info("Starting Prisma bot...")

    # Create application
    app = Application.builder().token(PRISMA_BOT_TOKEN).build()

    # Add handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("prompt", prompt_command))

    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        handle_message
    ))

    app.add_handler(MessageHandler(
        filters.PHOTO,
        handle_photo
    ))

    # Add proactive job
    job_queue = app.job_queue
    job_queue.run_repeating(
        proactive_check,
        interval=PROACTIVE_CHECK_MINUTES * 60,
        first=60  # Start after 1 minute
    )

    # Schedule daily check-ins
    if PYTZ_AVAILABLE:
        tz = pytz.timezone(TIMEZONE)
        for checkin in DAILY_CHECKINS:
            checkin_time = time(
                hour=checkin["hour"],
                minute=checkin["minute"],
                tzinfo=tz
            )
            job_queue.run_daily(
                daily_checkin,
                time=checkin_time,
                data={"type": checkin["type"]}
            )
            logger.info(f"Scheduled {checkin['type']} check-in at {checkin['hour']:02d}:{checkin['minute']:02d} {TIMEZONE}")
    else:
        logger.warning("pytz not available, daily check-ins disabled")

    logger.info(f"{BOT_NAME} bot starting with proactive kicker and daily check-ins...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
