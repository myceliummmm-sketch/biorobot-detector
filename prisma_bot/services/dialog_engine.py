"""
Dialog Engine - State Machine for IDEA phase questionnaire.
Manages the conversation flow for filling out cards.
"""

import logging
import json
from typing import Optional, Dict, Tuple
from dataclasses import dataclass
from enum import Enum

from data.questions import (
    IDEA_CARDS_ORDER,
    get_card_questions,
    get_question,
    get_next_card,
    format_question_message
)

logger = logging.getLogger(__name__)


class DialogState(Enum):
    """Possible states in the dialog flow"""
    IDLE = "idle"                    # Not in a dialog
    AWAITING_ANSWER = "awaiting"     # Waiting for user's answer
    CONFIRMING = "confirming"        # Waiting for card confirmation
    COMPLETED = "completed"          # All cards done


@dataclass
class DialogContext:
    """Current dialog context for a project"""
    project_id: str
    current_card: str           # product/problem/audience/value/vision
    current_question: int       # 1-5
    state: DialogState
    draft_answers: Dict         # {field: answer}


class DialogEngine:
    """
    State Machine for managing IDEA phase dialogs.

    Flow:
    1. User sends message to #idea topic
    2. Engine checks current state from DB
    3. Processes answer, saves to draft
    4. Asks next question OR prompts for confirmation
    5. On confirmation, finalizes card and moves to next
    """

    def __init__(self, supabase_client=None):
        """
        Initialize DialogEngine.

        Args:
            supabase_client: Supabase client for database operations
        """
        self.supabase = supabase_client
        self._contexts: Dict[str, DialogContext] = {}  # In-memory cache
        logger.info("DialogEngine initialized")

    # ==================== ROUTING ====================

    def should_handle_message(self, project_id: str, thread_id: int) -> bool:
        """
        Check if this message should be handled by DialogEngine.

        Args:
            project_id: Project/workspace ID
            thread_id: Telegram message_thread_id

        Returns:
            True if this is the #idea topic for this project
        """
        if not self.supabase:
            return False

        try:
            # Get project topics from database
            result = self.supabase.table("projects")\
                .select("topics")\
                .eq("id", project_id)\
                .execute()

            if not result.data:
                return False

            topics = result.data[0].get("topics", {})
            idea_thread_id = topics.get("idea_thread_id")

            return idea_thread_id == thread_id

        except Exception as e:
            logger.error(f"Error checking topic: {e}")
            return False

    def get_project_by_chat(self, chat_id: int) -> Optional[str]:
        """
        Get project ID by Telegram chat ID.

        Args:
            chat_id: Telegram chat_id

        Returns:
            Project ID or None
        """
        if not self.supabase:
            return None

        try:
            result = self.supabase.table("projects")\
                .select("id")\
                .eq("telegram_group_id", chat_id)\
                .execute()

            return result.data[0]["id"] if result.data else None

        except Exception as e:
            logger.error(f"Error getting project: {e}")
            return None

    # ==================== STATE MANAGEMENT ====================

    def get_dialog_state(self, project_id: str) -> Optional[DialogContext]:
        """
        Get current dialog state from database.

        Args:
            project_id: Project ID

        Returns:
            DialogContext or None if no active dialog
        """
        # Check in-memory cache first
        if project_id in self._contexts:
            return self._contexts[project_id]

        if not self.supabase:
            return None

        try:
            result = self.supabase.table("dialog_states")\
                .select("*")\
                .eq("project_id", project_id)\
                .execute()

            if not result.data:
                return None

            data = result.data[0]
            context = DialogContext(
                project_id=project_id,
                current_card=data.get("current_card", "product"),
                current_question=data.get("current_question", 1),
                state=DialogState(data.get("state", "idle")),
                draft_answers=data.get("draft_answers", {})
            )

            # Cache it
            self._contexts[project_id] = context
            return context

        except Exception as e:
            logger.error(f"Error getting dialog state: {e}")
            return None

    def save_dialog_state(self, context: DialogContext) -> bool:
        """
        Save dialog state to database.

        Args:
            context: DialogContext to save

        Returns:
            True if successful
        """
        if not self.supabase:
            return False

        try:
            data = {
                "project_id": context.project_id,
                "current_card": context.current_card,
                "current_question": context.current_question,
                "state": context.state.value,
                "draft_answers": context.draft_answers
            }

            # Upsert - insert or update
            self.supabase.table("dialog_states")\
                .upsert(data, on_conflict="project_id")\
                .execute()

            # Update cache
            self._contexts[context.project_id] = context
            return True

        except Exception as e:
            logger.error(f"Error saving dialog state: {e}")
            return False

    def start_dialog(self, project_id: str) -> Tuple[bool, str]:
        """
        Start a new dialog for a project.

        Args:
            project_id: Project ID

        Returns:
            (success, first_question_message)
        """
        # Create initial context
        context = DialogContext(
            project_id=project_id,
            current_card="product",
            current_question=1,
            state=DialogState.AWAITING_ANSWER,
            draft_answers={}
        )

        if self.save_dialog_state(context):
            question_msg = format_question_message("product", 1)
            return True, question_msg

        return False, "Ошибка при старте диалога"

    # ==================== MESSAGE PROCESSING ====================

    def process_message(self, project_id: str, user_message: str, user_name: str = "User") -> Tuple[str, Optional[Dict]]:
        """
        Process incoming user message.

        This is the main entry point for handling user input.

        Args:
            project_id: Project ID
            user_message: User's message text
            user_name: User's display name

        Returns:
            (response_message, optional_keyboard_data)
        """
        context = self.get_dialog_state(project_id)

        # No active dialog - start one
        if not context:
            success, msg = self.start_dialog(project_id)
            if success:
                return f"Привет, {user_name}! Давай заполним карточки для твоего проекта.\n\n{msg}", None
            return msg, None

        # Handle based on current state
        if context.state == DialogState.AWAITING_ANSWER:
            return self._handle_answer(context, user_message)

        elif context.state == DialogState.CONFIRMING:
            return self._handle_confirmation(context, user_message)

        elif context.state == DialogState.COMPLETED:
            return "🎉 Фаза IDEA завершена! Все карточки заполнены.", None

        else:
            return "Что-то пошло не так. Попробуй /restart", None

    def _handle_answer(self, context: DialogContext, answer: str) -> Tuple[str, Optional[Dict]]:
        """Handle user's answer to a question"""

        # Get current question to save the field name
        question = get_question(context.current_card, context.current_question)
        if question:
            # Save answer to draft
            context.draft_answers[question["field"]] = answer.strip()

        # Check if more questions in this card
        if context.current_question < 5:
            # Move to next question
            context.current_question += 1
            context.state = DialogState.AWAITING_ANSWER
            self.save_dialog_state(context)

            next_question = format_question_message(context.current_card, context.current_question)
            return f"✓ Записал.\n\n{next_question}", None

        else:
            # Card complete - ask for confirmation
            context.state = DialogState.CONFIRMING
            self.save_dialog_state(context)

            summary = self._format_card_summary(context)
            keyboard = {
                "inline_keyboard": [[
                    {"text": "✅ Фиксируем", "callback_data": f"confirm_card:{context.project_id}"},
                    {"text": "🔄 Переделать", "callback_data": f"redo_card:{context.project_id}"}
                ]]
            }

            card_info = get_card_questions(context.current_card)
            emoji = card_info["emoji"] if card_info else "📋"
            title = card_info["title"] if card_info else context.current_card

            return f"✓ Записал.\n\n{emoji} **Карточка {title} готова!**\n\n{summary}\n\nФиксируем?", keyboard

    def _handle_confirmation(self, context: DialogContext, response: str) -> Tuple[str, Optional[Dict]]:
        """Handle confirmation response (text-based fallback)"""

        response_lower = response.lower().strip()

        if response_lower in ["да", "yes", "ок", "ok", "фиксируем", "подтверждаю"]:
            return self.confirm_card(context.project_id)

        elif response_lower in ["нет", "no", "переделать", "заново"]:
            return self.redo_card(context.project_id)

        else:
            return "Напиши 'да' чтобы зафиксировать карту, или 'нет' чтобы переделать.", None

    # ==================== CARD ACTIONS ====================

    def confirm_card(self, project_id: str) -> Tuple[str, Optional[Dict]]:
        """
        Confirm and save current card, move to next.

        Args:
            project_id: Project ID

        Returns:
            (response_message, keyboard_data)
        """
        context = self.get_dialog_state(project_id)
        if not context:
            return "Диалог не найден. Начни заново с /start", None

        # Save card to database
        self._save_card_to_db(context)

        # Get next card
        next_card = get_next_card(context.current_card)

        if next_card:
            # Move to next card
            context.current_card = next_card
            context.current_question = 1
            context.state = DialogState.AWAITING_ANSWER
            context.draft_answers = {}
            self.save_dialog_state(context)

            next_question = format_question_message(next_card, 1)
            card_info = get_card_questions(context.current_card)

            cards_done = IDEA_CARDS_ORDER.index(next_card)
            progress = f"[{'●' * cards_done}{'○' * (5 - cards_done)}]"

            return f"✅ Карточка сохранена!\n\n{progress} {cards_done}/5 карт\n\n{next_question}", None

        else:
            # All cards done!
            context.state = DialogState.COMPLETED
            self.save_dialog_state(context)

            return "🎉 **Поздравляю!** Фаза IDEA завершена!\n\nВсе 5 карточек заполнены. Теперь можно переходить к фазе Research.\n\n+20 Spores за завершение фазы! 🌿", None

    def redo_card(self, project_id: str) -> Tuple[str, Optional[Dict]]:
        """
        Restart current card from beginning.

        Args:
            project_id: Project ID

        Returns:
            (response_message, keyboard_data)
        """
        context = self.get_dialog_state(project_id)
        if not context:
            return "Диалог не найден", None

        # Reset card progress
        context.current_question = 1
        context.state = DialogState.AWAITING_ANSWER
        context.draft_answers = {}
        self.save_dialog_state(context)

        first_question = format_question_message(context.current_card, 1)
        return f"🔄 Начинаем карточку заново.\n\n{first_question}", None

    def _save_card_to_db(self, context: DialogContext) -> bool:
        """Save completed card to database"""
        if not self.supabase:
            logger.warning("No Supabase client, skipping card save")
            return False

        try:
            card_data = {
                "project_id": context.project_id,
                "type": context.current_card,
                "content": context.draft_answers,
                "stage": "idea",
                "status": "done",
                "fill_rate": 100
            }

            self.supabase.table("cards")\
                .upsert(card_data, on_conflict="project_id,type")\
                .execute()

            logger.info(f"Saved card {context.current_card} for project {context.project_id}")
            return True

        except Exception as e:
            logger.error(f"Error saving card: {e}")
            return False

    # ==================== FORMATTING ====================

    def _format_card_summary(self, context: DialogContext) -> str:
        """Format card answers as summary"""
        card_info = get_card_questions(context.current_card)
        if not card_info:
            return "Ответы сохранены."

        lines = []
        for q in card_info["questions"]:
            field = q["field"]
            answer = context.draft_answers.get(field, "—")
            # Truncate long answers
            if len(answer) > 100:
                answer = answer[:100] + "..."
            lines.append(f"**{q['text'][:40]}...**\n_{answer}_")

        return "\n\n".join(lines)

    def get_progress(self, project_id: str) -> Dict:
        """Get dialog progress for a project"""
        context = self.get_dialog_state(project_id)
        if not context:
            return {"started": False}

        current_idx = IDEA_CARDS_ORDER.index(context.current_card) if context.current_card in IDEA_CARDS_ORDER else 0

        return {
            "started": True,
            "current_card": context.current_card,
            "current_question": context.current_question,
            "cards_completed": current_idx,
            "total_cards": 5,
            "state": context.state.value,
            "progress_percent": int((current_idx * 5 + context.current_question - 1) / 25 * 100)
        }


# ==================== SINGLETON ====================

_engine: Optional[DialogEngine] = None


def get_dialog_engine(supabase_client=None) -> DialogEngine:
    """Get or create DialogEngine singleton"""
    global _engine
    if _engine is None:
        _engine = DialogEngine(supabase_client)
    elif supabase_client and not _engine.supabase:
        _engine.supabase = supabase_client
    return _engine
