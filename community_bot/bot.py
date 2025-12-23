import logging
import random
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from config import (
    COMMUNITY_BOT_TOKEN,
    COMMUNITY_CHAT_ID,
    RESPONSE_PROBABILITY,
    TRIGGER_KEYWORDS,
    BOT_NAME
)
from gemini_client import get_gemini_client

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


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

    # Skip bot's own messages
    if user.is_bot:
        logger.info("Skipping bot message")
        return

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


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    await update.message.reply_text(
        f"Привет, биоробот! Я {BOT_NAME} — твой ироничный друг из мира грибниц.\n\n"
        "Буду тусить в чате, подкалывать и иногда даже помогать. "
        "Если что-то про Mycelium Cards хочешь узнать — спрашивай, расскажу как не быть NPC в своей жизни"
    )


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /status command - show bot status"""
    gemini = get_gemini_client()
    chat_count = len(gemini.chat_histories)

    await update.message.reply_text(
        f"Статус: Живой, как мицелий в лесу\n"
        f"Активных чатов в памяти: {chat_count}\n"
        f"Вероятность ответа: {RESPONSE_PROBABILITY * 100:.0f}%"
    )


async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /clear command - clear chat history"""
    chat_id = update.message.chat_id
    gemini = get_gemini_client()
    gemini.clear_history(chat_id)

    await update.message.reply_text("Память очищена. Кто вы все такие?")


def main():
    """Start the community bot"""
    if not COMMUNITY_BOT_TOKEN:
        logger.error("COMMUNITY_BOT_TOKEN not found!")
        raise ValueError("COMMUNITY_BOT_TOKEN is required. Set it in .env file.")

    logger.info("Starting community bot...")

    # Create application
    app = Application.builder().token(COMMUNITY_BOT_TOKEN).build()

    # Add handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("clear", clear_command))

    # Message handler for group chats
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        handle_message
    ))

    # Start polling
    logger.info(f"{BOT_NAME} bot starting... Press Ctrl+C to stop.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
