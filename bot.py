import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

from config import BOT_TOKEN, DATABASE_URL
from database import init_db
from handlers import start_handler, quiz_result_handler, video_handler

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def main():
    """Start the bot"""
    # Validate config
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN not found in environment variables!")
        raise ValueError("BOT_TOKEN is required. Set it in .env file.")

    # Initialize database
    logger.info("Initializing database...")
    init_db(DATABASE_URL)

    # Create application
    logger.info("Creating bot application...")
    app = Application.builder().token(BOT_TOKEN).build()

    # Add handlers
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(MessageHandler(
        filters.StatusUpdate.WEB_APP_DATA,
        quiz_result_handler
    ))
    app.add_handler(MessageHandler(filters.VIDEO, video_handler))

    # Start polling
    logger.info("Bot starting... Press Ctrl+C to stop.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
