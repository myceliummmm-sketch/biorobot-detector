import logging
import random
import asyncio
import io
from datetime import time
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

try:
    import pytz
    PYTZ_AVAILABLE = True
except ImportError:
    PYTZ_AVAILABLE = False

from config import (
    COMMUNITY_BOT_TOKEN,
    COMMUNITY_CHAT_ID,
    RESPONSE_PROBABILITY,
    TRIGGER_KEYWORDS,
    BOT_NAME
)
from gemini_client import get_gemini_client
from daily_card import get_card_generator

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Timezone for Spain
TIMEZONE = "Europe/Madrid"


async def handle_new_member_intro(update: Update, context: ContextTypes.DEFAULT_TYPE, intro_data: dict):
    """Handle new member's response to welcome questions - develop dialogue about their project"""
    message = update.message
    user = message.from_user
    chat_id = message.chat_id
    user_name = intro_data.get("name", user.first_name)

    logger.info(f"Processing intro from {user_name}: {message.text[:100]}")

    # Show typing indicator
    await context.bot.send_chat_action(chat_id=chat_id, action="typing")
    await asyncio.sleep(random.uniform(1.5, 3.0))

    # Generate contextual response with Gemini
    try:
        gemini = get_gemini_client()

        intro_prompt = f"""Ты Toxic — привратник лобби Syndicate Builders. Новый участник {user_name} ответил на твои вопросы о проекте/экспертизе:

"{message.text}"

Твоя задача:
1. Проанализировать ответ — есть ли у человека реальный проект или экспертиза
2. Задать уточняющие вопросы если нужно
3. Если проект интересный — похвалить и спросить детали
4. Если пока нет проекта — спросить что хочет построить
5. Если есть экспертиза — спросить как может помочь другим

Отвечай в своём стиле: прямо, с иронией, но дружелюбно. 2-4 предложения.
Если ответ крутой — можешь намекнуть что такие люди нам нужны внутри."""

        response = await gemini.generate_response(chat_id, user_name, intro_prompt)
        await message.reply_text(response)

        # Update intro stage
        context.bot_data["pending_intros"][user.id]["stage"] = "in_dialogue"
        context.bot_data["pending_intros"][user.id]["messages"] = intro_data.get("messages", 0) + 1

        # After 3 exchanges, remove from pending (dialogue complete)
        if context.bot_data["pending_intros"][user.id]["messages"] >= 3:
            del context.bot_data["pending_intros"][user.id]
            logger.info(f"Completed intro dialogue with {user_name}")

    except Exception as e:
        logger.error(f"Error in intro dialogue: {e}")
        await message.reply_text("хм, интересно. расскажи подробнее — что конкретно строишь или хочешь построить?")


def should_respond(message_text: str, is_reply_to_bot: bool, is_mention: bool) -> bool:
    """Determine if bot should respond to this message"""
    # Always respond to direct replies and mentions
    if is_reply_to_bot or is_mention:
        return True

    # Check for trigger keywords
    text_lower = message_text.lower()
    has_trigger = any(keyword in text_lower for keyword in TRIGGER_KEYWORDS)

    if has_trigger:
        # Higher probability for trigger keywords
        return random.random() < 0.7

    # Random responses based on probability
    return random.random() < RESPONSE_PROBABILITY


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming messages in group chat"""
    # Log ALL incoming updates for debugging
    logger.info(f"=== RECEIVED UPDATE: {update}")

    message = update.message
    if not message or not message.text:
        logger.info("No message or text, skipping")
        return

    chat_id = message.chat_id
    user = message.from_user

    logger.info(f"Message from {user.first_name} in chat {chat_id}: {message.text[:100]}")

    # Skip bot's own messages (but allow channel forwards)
    if user.is_bot and user.id == (await context.bot.get_me()).id:
        logger.info("Skipping own bot message")
        return

    # Check if this is a new member responding to welcome questions
    pending_intros = context.bot_data.get("pending_intros", {})
    is_new_member_intro = user.id in pending_intros

    # Check if this is a reply to the bot
    is_reply_to_bot = (
        message.reply_to_message and
        message.reply_to_message.from_user and
        message.reply_to_message.from_user.id == context.bot.id
    )

    # Check if bot is mentioned by @username
    bot_username = (await context.bot.get_me()).username
    is_mention = f"@{bot_username}" in message.text if bot_username else False

    # Check if bot is called by name (toxic, токсик)
    text_lower = message.text.lower()
    is_called_by_name = any(name in text_lower for name in ["toxic", "токсик", "токсика", "токсику"])

    # Always respond to new member intros
    if is_new_member_intro and is_reply_to_bot:
        await handle_new_member_intro(update, context, pending_intros[user.id])
        return

    # Decide if we should respond
    if not should_respond(message.text, is_reply_to_bot, is_mention or is_called_by_name):
        return

    logger.info(f"Responding to message from {user.first_name}: {message.text[:50]}...")

    # Show typing indicator
    await context.bot.send_chat_action(chat_id=chat_id, action="typing")

    # Small delay to seem more natural
    await asyncio.sleep(random.uniform(1.0, 3.0))

    # Generate response with Gemini
    try:
        gemini = get_gemini_client()
        user_name = user.first_name or user.username or "Аноним"
        response = await gemini.generate_response(chat_id, user_name, message.text)

        # Send response
        await message.reply_text(response)
        logger.info(f"Sent response: {response[:50]}...")

    except Exception as e:
        logger.error(f"Error generating response: {e}")


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming photos in group chat"""
    message = update.message
    if not message or not message.photo:
        return

    chat_id = message.chat_id
    user = message.from_user

    # Skip bot's own messages
    if user.is_bot and user.id == (await context.bot.get_me()).id:
        return

    # Check if bot should respond to this photo
    caption = message.caption or ""
    is_reply_to_bot = (
        message.reply_to_message and
        message.reply_to_message.from_user and
        message.reply_to_message.from_user.id == context.bot.id
    )

    bot_username = (await context.bot.get_me()).username
    is_mention = f"@{bot_username}" in caption if bot_username else False

    text_lower = caption.lower()
    is_called_by_name = any(name in text_lower for name in ["toxic", "токсик", "токсика", "токсику"])

    # Only respond to photos if explicitly mentioned or replied to
    if not (is_reply_to_bot or is_mention or is_called_by_name):
        # Small random chance to comment on photos anyway
        if random.random() > 0.1:  # 10% chance
            return

    logger.info(f"Processing photo from {user.first_name}")

    # Show typing indicator
    await context.bot.send_chat_action(chat_id=chat_id, action="typing")

    try:
        # Get the largest photo
        photo = message.photo[-1]
        file = await context.bot.get_file(photo.file_id)

        # Download photo bytes
        photo_bytes = await file.download_as_bytearray()

        gemini = get_gemini_client()
        user_name = user.first_name or user.username or "Аноним"

        # Generate response with image
        response = await gemini.generate_response_with_image(
            chat_id, user_name, caption or "что скажешь про это фото?", bytes(photo_bytes)
        )

        await message.reply_text(response)
        logger.info(f"Sent photo response: {response[:50]}...")

    except Exception as e:
        logger.error(f"Error processing photo: {e}")


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    await update.message.reply_text(
        f"☢️ Это лобби Syndicate Builders.\n\n"
        f"Я {BOT_NAME} — привратник. Здесь собираются те, кто строит проекты, а не мечтает о них.\n\n"
        "Внутрь попадают:\n"
        "🔹 Билдеры с реальными проектами\n"
        "🔹 Эксперты с полезными скиллами\n"
        "🔹 Вайбкодеры с крутыми идеями\n\n"
        "Расскажи о себе — и посмотрим, готов ли ты к грибнице 🍄"
    )


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /status command - show bot status"""
    gemini = get_gemini_client()
    chat_count = len(gemini.chat_histories)

    await update.message.reply_text(
        f"Статус: Живой, как мицелий в лесу\n"
        f"Активных чатов в памяти: {chat_count}\n"
        f"Вероятность ответа: {RESPONSE_PROBABILITY * 100:.0f}%\n"
        f"Карточка дня: 17:00 (Madrid)"
    )


async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /clear command - clear chat history"""
    chat_id = update.message.chat_id
    gemini = get_gemini_client()
    gemini.clear_history(chat_id)

    await update.message.reply_text("Память очищена. Кто вы все такие?")


async def card_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /card command - generate and send daily card manually"""
    chat_id = update.message.chat_id

    await update.message.reply_text("⏳ генерирую карточку дня...")

    try:
        gemini = get_gemini_client()
        card_gen = get_card_generator(gemini)

        caption, image_bytes = await card_gen.generate_daily_card()

        if caption:
            if image_bytes:
                # Send image first with short intro
                await context.bot.send_photo(
                    chat_id=chat_id,
                    photo=io.BytesIO(image_bytes),
                    caption="🎴 карточка дня от токсика"
                )
                # Then send full text
                await context.bot.send_message(chat_id=chat_id, text=caption)
            else:
                # Send text only
                await context.bot.send_message(chat_id=chat_id, text=caption)

            logger.info("Daily card sent successfully")
        else:
            await update.message.reply_text("❌ не удалось сгенерировать карточку")

    except Exception as e:
        logger.error(f"Error generating card: {e}")
        await update.message.reply_text(f"❌ ошибка: {str(e)[:100]}")


async def daily_card_job(context: ContextTypes.DEFAULT_TYPE):
    """Scheduled job to post daily card at 17:00"""
    if not COMMUNITY_CHAT_ID:
        logger.warning("COMMUNITY_CHAT_ID not set, skipping daily card")
        return

    logger.info("Running daily card job...")

    try:
        gemini = get_gemini_client()
        card_gen = get_card_generator(gemini)

        caption, image_bytes = await card_gen.generate_daily_card()

        if caption:
            if image_bytes:
                # Send image first with short intro
                await context.bot.send_photo(
                    chat_id=COMMUNITY_CHAT_ID,
                    photo=io.BytesIO(image_bytes),
                    caption="🎴 карточка дня от токсика"
                )
                # Then send full text
                await context.bot.send_message(chat_id=COMMUNITY_CHAT_ID, text=caption)
            else:
                await context.bot.send_message(chat_id=COMMUNITY_CHAT_ID, text=caption)

            logger.info("Daily card posted to community chat")
        else:
            logger.error("Failed to generate daily card")

    except Exception as e:
        logger.error(f"Error in daily card job: {e}")


async def welcome_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Welcome new members to the lobby - ask about projects and expertise"""
    message = update.message
    if not message or not message.new_chat_members:
        return

    chat_id = message.chat_id

    for new_member in message.new_chat_members:
        # Skip if bot joined
        if new_member.is_bot:
            continue

        user_name = new_member.first_name or new_member.username or "биоробот"

        logger.info(f"New member joined lobby: {user_name}")

        # Show typing indicator
        await context.bot.send_chat_action(chat_id=chat_id, action="typing")
        await asyncio.sleep(random.uniform(1.0, 2.0))

        # Welcome message as lobby gatekeeper
        welcome_text = f"""☢️ о, {user_name}! Добро пожаловать в лобби Syndicate.

Здесь собираются билдеры — те, кто строит, а не просто мечтает.

Расскажи о себе:
🔹 Есть проект? Над чем работаешь?
🔹 Какая помощь нужна?
🔹 Какой экспертизой можешь поделиться?

Внутрь пускаем тех, кто реально строит или может усилить команду. Покажи что у тебя есть — и поговорим 🍄"""

        await message.reply_text(welcome_text)

        # Store that we're waiting for intro from this user
        if "pending_intros" not in context.bot_data:
            context.bot_data["pending_intros"] = {}
        context.bot_data["pending_intros"][new_member.id] = {
            "name": user_name,
            "chat_id": chat_id,
            "stage": "awaiting_intro"
        }


def main():
    """Start the community bot"""
    if not COMMUNITY_BOT_TOKEN:
        logger.error("COMMUNITY_BOT_TOKEN not found!")
        raise ValueError("COMMUNITY_BOT_TOKEN is required. Set it in .env file.")

    logger.info("Starting community bot...")

    # Create application with job queue
    app = Application.builder().token(COMMUNITY_BOT_TOKEN).build()

    # Add handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("clear", clear_command))
    app.add_handler(CommandHandler("card", card_command))

    # Message handler for group chats
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        handle_message
    ))

    # Photo handler
    app.add_handler(MessageHandler(
        filters.PHOTO,
        handle_photo
    ))

    # New member welcome handler
    app.add_handler(MessageHandler(
        filters.StatusUpdate.NEW_CHAT_MEMBERS,
        welcome_new_member
    ))

    # Schedule daily card at 17:00 Madrid time
    job_queue = app.job_queue
    if PYTZ_AVAILABLE:
        tz = pytz.timezone(TIMEZONE)
        job_queue.run_daily(
            daily_card_job,
            time=time(hour=17, minute=0, tzinfo=tz),
            name="daily_card"
        )
        logger.info("Scheduled daily card job at 17:00 Madrid time")
    else:
        # Fallback: UTC+1 approximately
        job_queue.run_daily(
            daily_card_job,
            time=time(hour=16, minute=0),  # UTC, roughly Spain
            name="daily_card"
        )
        logger.warning("pytz not available, using UTC time for daily card")

    # Start polling
    logger.info(f"{BOT_NAME} bot starting... Press Ctrl+C to stop.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
