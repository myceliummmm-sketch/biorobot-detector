import logging
import random
import asyncio
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from config import (
    PRISMA_BOT_TOKEN,
    BOT_NAME,
    BOT_NAMES,
    TRIGGER_KEYWORDS,
    SILENCE_KICK_HOURS,
    SILENCE_ALARM_HOURS,
    RANDOM_INSIGHT_CHANCE,
    PROACTIVE_CHECK_MINUTES
)
from database import (
    init_db,
    log_message,
    update_last_message_time,
    get_silence_duration,
    update_last_kick_time,
    get_all_active_chats
)
from gemini_client import get_prisma_client

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
        "💎 привет, биоробот. я prisma — ai со-основатель mycelium.\n\n"
        "буду следить за вашим прогрессом, пинать если заснете, "
        "и убивать zombie-проекты.\n\n"
        "тегни меня когда нужен совет или когда хочешь поспорить ⚡"
    )


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /status"""
    chat_id = update.message.chat_id
    silence = get_silence_duration(chat_id)

    status = "активен" if silence < SILENCE_KICK_HOURS else "засыпает" if silence < SILENCE_ALARM_HOURS else "в коме"

    await update.message.reply_text(
        f"💎 статус чата: {status}\n"
        f"⏱ тишина: {silence:.1f} часов\n"
        f"⚡ порог пинка: {SILENCE_KICK_HOURS}ч\n"
        f"🚨 порог тревоги: {SILENCE_ALARM_HOURS}ч"
    )


async def proactive_check(context: ContextTypes.DEFAULT_TYPE):
    """Proactive check - kick silent chats"""
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

    logger.info(f"{BOT_NAME} bot starting with proactive kicker...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
