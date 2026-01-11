"""
Кузя - домашний бот-помощник для семьи
Отвечает на вопросы бабушки и мамы как заботливый внук
"""

import logging
import random
import asyncio
import os
from datetime import time
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

try:
    import pytz
    PYTZ_AVAILABLE = True
except ImportError:
    PYTZ_AVAILABLE = False

from config import (
    KUZYA_BOT_TOKEN, BOT_NAME, BOT_NAMES,
    TIMEZONE, CHECKIN_MESSAGES, CHECKIN_TIMES
)
from gemini_client import get_kuzya_client
from database import register_chat, get_all_active_chats, remove_chat, log_message

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages"""
    message = update.message
    if not message or not message.text:
        return

    chat_id = message.chat_id
    user = message.from_user

    if user.is_bot:
        return

    user_name = user.first_name or "друг"
    text = message.text

    logger.info(f"Message from {user_name}: {text[:50]}...")

    # Check if should respond
    text_lower = text.lower()

    is_reply_to_bot = (
        message.reply_to_message and
        message.reply_to_message.from_user and
        message.reply_to_message.from_user.id == context.bot.id
    )
    is_called = any(name in text_lower for name in BOT_NAMES)
    bot_username = context.bot.username
    is_mention = f"@{bot_username}".lower() in text_lower if bot_username else False
    is_question = "?" in text

    # In private chat - always respond
    # In group - respond to name calls, mentions, replies, or sometimes questions
    if message.chat.type == "private":
        pass  # Always respond
    elif is_reply_to_bot or is_called or is_mention:
        pass  # Respond to direct calls
    elif is_question and random.random() < 0.2:
        pass  # 20% chance on questions
    else:
        logger.debug(f"Skipping message, no trigger found in: {text[:30]}")
        return

    # Register chat for check-ins
    chat_title = message.chat.title if message.chat.type != "private" else user_name
    register_chat(chat_id, chat_title)

    # Show typing
    await context.bot.send_chat_action(chat_id=chat_id, action="typing")
    await asyncio.sleep(random.uniform(0.5, 1.5))

    try:
        # Log user message
        log_message(chat_id, user_name, "user", text)

        kuzya = get_kuzya_client()
        response = await kuzya.generate_response(chat_id, user_name, text)

        # Log bot response
        log_message(chat_id, BOT_NAME, "assistant", response)

        await message.reply_text(response)
        logger.info(f"Sent response: {response[:50]}...")

    except Exception as e:
        logger.error(f"Error: {e}")
        await message.reply_text("Простите, что-то пошло не так. Попробуйте ещё раз?")


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle voice messages - transcribe and respond"""
    message = update.message
    if not message or not message.voice:
        return

    chat_id = message.chat_id
    user = message.from_user

    if user.is_bot:
        return

    user_name = user.first_name or "друг"
    duration = message.voice.duration or 0

    logger.info(f"Voice from {user_name}, {duration}s")

    # Notify about processing
    if duration > 30:
        await message.reply_text("Минутку, расшифровываю голосовое...")

    try:
        # Download voice
        voice = message.voice
        file = await context.bot.get_file(voice.file_id)
        voice_path = f"/tmp/kuzya_voice_{voice.file_id}.ogg"
        await file.download_to_drive(voice_path)

        text = None

        # Try OpenAI Whisper
        openai_key = os.environ.get("OPENAI_API_KEY")
        if openai_key:
            try:
                import requests
                with open(voice_path, "rb") as audio:
                    response = requests.post(
                        "https://api.openai.com/v1/audio/transcriptions",
                        headers={"Authorization": f"Bearer {openai_key}"},
                        files={"file": audio},
                        data={"model": "whisper-1", "language": "ru"},
                        timeout=60
                    )
                if response.ok:
                    text = response.json().get("text", "").strip()
            except Exception as e:
                logger.warning(f"Whisper error: {e}")

        # Fallback to Google Speech
        if not text:
            try:
                import subprocess
                import speech_recognition as sr

                wav_path = f"/tmp/kuzya_voice_{voice.file_id}.wav"
                subprocess.run(
                    ["ffmpeg", "-y", "-i", voice_path, "-ar", "16000", "-ac", "1", wav_path],
                    capture_output=True, timeout=30
                )

                recognizer = sr.Recognizer()
                with sr.AudioFile(wav_path) as source:
                    audio = recognizer.record(source)
                text = recognizer.recognize_google(audio, language="ru-RU")

                if os.path.exists(wav_path):
                    os.unlink(wav_path)

            except Exception as e:
                logger.warning(f"Google Speech error: {e}")

        # Cleanup
        if os.path.exists(voice_path):
            os.unlink(voice_path)

        if not text:
            await message.reply_text("Простите, не смог расшифровать. Попробуйте записать ещё раз?")
            return

        # Log and respond
        log_message(chat_id, user_name, "user", f"[голосовое] {text}")

        await context.bot.send_chat_action(chat_id=chat_id, action="typing")

        kuzya = get_kuzya_client()
        response = await kuzya.generate_response(chat_id, user_name, text)

        log_message(chat_id, BOT_NAME, "assistant", response)

        # Send with transcription
        preview = text[:300] + "..." if len(text) > 300 else text
        await message.reply_text(f"🎤 Вы сказали: \"{preview}\"\n\n{response}")

    except Exception as e:
        logger.error(f"Voice error: {e}")
        await message.reply_text("Простите, не получилось обработать голосовое.")


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle photos"""
    message = update.message
    if not message or not message.photo:
        return

    chat_id = message.chat_id
    user = message.from_user

    if user.is_bot:
        return

    user_name = user.first_name or "друг"
    caption = message.caption or ""

    # Check if should respond to photo
    caption_lower = caption.lower()
    is_reply_to_bot = (
        message.reply_to_message and
        message.reply_to_message.from_user and
        message.reply_to_message.from_user.id == context.bot.id
    )
    is_called = any(name in caption_lower for name in BOT_NAMES)

    # In private - always, in group - need to be called
    if message.chat.type != "private" and not (is_reply_to_bot or is_called):
        return

    logger.info(f"Photo from {user_name}")

    await context.bot.send_chat_action(chat_id=chat_id, action="typing")

    try:
        photo = message.photo[-1]
        file = await context.bot.get_file(photo.file_id)
        photo_bytes = await file.download_as_bytearray()

        # Log user photo
        log_message(chat_id, user_name, "user", f"[фото] {caption}" if caption else "[фото]")

        kuzya = get_kuzya_client()
        response = await kuzya.generate_response_with_image(
            chat_id, user_name, caption, bytes(photo_bytes)
        )

        # Log bot response
        log_message(chat_id, BOT_NAME, "assistant", response)

        await message.reply_text(response)

    except Exception as e:
        logger.error(f"Photo error: {e}")
        await message.reply_text("Не смог разобрать фотографию, простите.")


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start"""
    user_name = update.effective_user.first_name or "друг"
    await update.message.reply_text(
        f"Привет, {user_name}! 👋\n\n"
        f"Я {BOT_NAME} — всегда на связи, спрашивай что угодно!\n\n"
        "Можно писать или отправлять голосовые — я всё пойму 🤗"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help"""
    await update.message.reply_text(
        f"Я {BOT_NAME}, вот что умею:\n\n"
        "💬 Отвечать на вопросы\n"
        "🎤 Понимать голосовые\n"
        "📷 Смотреть фотки и рассказывать что на них\n\n"
        "Просто напиши или запиши голосовое! 😊"
    )


async def daily_checkin(context: ContextTypes.DEFAULT_TYPE):
    """Send daily check-in message to all active chats"""
    active_chats = get_all_active_chats()

    if not active_chats:
        logger.info("No active chats for check-in")
        return

    for chat_id in active_chats:
        try:
            message = random.choice(CHECKIN_MESSAGES)
            await context.bot.send_message(chat_id=chat_id, text=message)
            logger.info(f"Sent check-in to {chat_id}: {message[:30]}...")
        except Exception as e:
            logger.error(f"Check-in error for {chat_id}: {e}")
            # If bot was blocked/kicked, remove from active chats
            if "bot was blocked" in str(e).lower() or "chat not found" in str(e).lower():
                remove_chat(chat_id)


def main():
    """Start Kuzya bot"""
    if not KUZYA_BOT_TOKEN:
        raise ValueError("KUZYA_BOT_TOKEN is required")

    logger.info(f"Starting {BOT_NAME} bot...")

    app = Application.builder().token(KUZYA_BOT_TOKEN).build()

    # Commands
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))

    # Messages
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))

    # Schedule daily check-ins to all active chats
    if PYTZ_AVAILABLE:
        job_queue = app.job_queue
        tz = pytz.timezone(TIMEZONE)

        for hour, minute in CHECKIN_TIMES:
            checkin_time = time(hour=hour, minute=minute, tzinfo=tz)
            job_queue.run_daily(daily_checkin, time=checkin_time)
            logger.info(f"Scheduled check-in at {hour:02d}:{minute:02d} {TIMEZONE}")
    else:
        logger.warning("pytz not available, daily check-ins disabled")

    logger.info(f"{BOT_NAME} starting... Press Ctrl+C to stop.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
