"""
Dialog Handler - Integration between Telegram bot and DialogEngine.
Handles routing messages to the correct topic handler.
"""

import logging
from typing import Optional, Tuple
from telegram import Update, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from .dialog_engine import get_dialog_engine, DialogEngine
from supabase_client import get_supabase

logger = logging.getLogger(__name__)


class DialogHandler:
    """
    Handles Telegram messages and routes them to DialogEngine.

    Usage in bot.py:
        dialog_handler = DialogHandler()

        async def handle_message(update, context):
            # Check if DialogEngine should handle this
            response = await dialog_handler.handle_message(update, context)
            if response:
                return  # DialogEngine handled it
            # ... rest of message handling
    """

    def __init__(self):
        self.engine: Optional[DialogEngine] = None

    def _get_engine(self) -> DialogEngine:
        """Lazy init of DialogEngine with Supabase"""
        if not self.engine:
            supabase = get_supabase()
            self.engine = get_dialog_engine(supabase)
        return self.engine

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
        """
        Handle incoming message if it's in an #idea topic.

        Args:
            update: Telegram Update object
            context: Bot context

        Returns:
            True if message was handled, False if should be passed to other handlers
        """
        message = update.message
        if not message or not message.text:
            return False

        chat_id = message.chat_id
        thread_id = message.message_thread_id

        # Only handle messages in topic threads
        if not thread_id:
            return False

        engine = self._get_engine()

        # Get project by chat_id
        project_id = engine.get_project_by_chat(chat_id)
        if not project_id:
            return False

        # Check if this is the #idea topic
        if not engine.should_handle_message(project_id, thread_id):
            return False

        # Route to DialogEngine
        user = message.from_user
        user_name = user.first_name or user.username or "User"

        response, keyboard_data = engine.process_message(
            project_id=project_id,
            user_message=message.text,
            user_name=user_name
        )

        # Send response
        reply_markup = None
        if keyboard_data:
            reply_markup = InlineKeyboardMarkup(keyboard_data["inline_keyboard"])

        await message.reply_text(
            response,
            parse_mode="Markdown",
            reply_markup=reply_markup
        )

        return True

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
        """
        Handle callback button presses from card confirmation.

        Args:
            update: Telegram Update object
            context: Bot context

        Returns:
            True if callback was handled
        """
        query = update.callback_query
        if not query or not query.data:
            return False

        data = query.data

        # Check if this is a dialog callback
        if not data.startswith(("confirm_card:", "redo_card:")):
            return False

        await query.answer()

        engine = self._get_engine()

        if data.startswith("confirm_card:"):
            project_id = data.split(":")[1]
            response, keyboard_data = engine.confirm_card(project_id)

        elif data.startswith("redo_card:"):
            project_id = data.split(":")[1]
            response, keyboard_data = engine.redo_card(project_id)

        else:
            return False

        # Edit message with response
        reply_markup = None
        if keyboard_data:
            reply_markup = InlineKeyboardMarkup(keyboard_data["inline_keyboard"])

        await query.edit_message_text(
            response,
            parse_mode="Markdown",
            reply_markup=reply_markup
        )

        return True


# ==================== COMMANDS ====================

async def start_idea_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /startidea - Start the IDEA phase questionnaire.

    This creates a new dialog if one doesn't exist.
    """
    message = update.message
    chat_id = message.chat_id

    supabase = get_supabase()
    engine = get_dialog_engine(supabase)

    # Get project
    project_id = engine.get_project_by_chat(chat_id)
    if not project_id:
        await message.reply_text(
            "❌ Проект не найден. Сначала создай воркспейс через веб-приложение."
        )
        return

    # Start dialog
    success, first_question = engine.start_dialog(project_id)

    if success:
        await message.reply_text(
            f"🚀 **Запускаем фазу IDEA!**\n\n"
            f"Сейчас заполним 5 карточек:\n"
            f"1. 🎯 Product\n"
            f"2. 🔥 Problem\n"
            f"3. 👥 Audience\n"
            f"4. 💎 Value\n"
            f"5. 🚀 Vision\n\n"
            f"Поехали!\n\n{first_question}",
            parse_mode="Markdown"
        )
    else:
        await message.reply_text("❌ Ошибка при запуске. Попробуй позже.")


async def idea_progress_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /ideaprogress - Show current progress in IDEA phase.
    """
    message = update.message
    chat_id = message.chat_id

    supabase = get_supabase()
    engine = get_dialog_engine(supabase)

    project_id = engine.get_project_by_chat(chat_id)
    if not project_id:
        await message.reply_text("❌ Проект не найден.")
        return

    progress = engine.get_progress(project_id)

    if not progress.get("started"):
        await message.reply_text(
            "Фаза IDEA ещё не начата.\n\n"
            "Используй /startidea чтобы начать."
        )
        return

    cards_done = progress["cards_completed"]
    current = progress["current_card"].title()
    question = progress["current_question"]
    percent = progress["progress_percent"]

    bar = "●" * cards_done + "○" * (5 - cards_done)

    await message.reply_text(
        f"📊 **Прогресс IDEA**\n\n"
        f"[{bar}] {cards_done}/5 карт\n\n"
        f"Текущая карта: **{current}**\n"
        f"Вопрос: {question}/5\n\n"
        f"Общий прогресс: {percent}%",
        parse_mode="Markdown"
    )


# Singleton handler
_dialog_handler: Optional[DialogHandler] = None


def get_dialog_handler() -> DialogHandler:
    """Get or create DialogHandler singleton"""
    global _dialog_handler
    if _dialog_handler is None:
        _dialog_handler = DialogHandler()
    return _dialog_handler
