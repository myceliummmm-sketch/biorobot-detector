import logging
import google.generativeai as genai
from config import GEMINI_API_KEY, get_system_prompt
from database import get_recent_messages

logger = logging.getLogger(__name__)


class PrismaGemini:
    def __init__(self):
        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is required")

        genai.configure(api_key=GEMINI_API_KEY)

        self.model = genai.GenerativeModel(
            model_name="models/gemini-3-flash-preview",
            generation_config={
                "temperature": 0.9,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 2048,
            }
        )
        logger.info("Prisma Gemini initialized")

    def _build_context(self, chat_id: int) -> str:
        """Build context from recent messages"""
        messages = get_recent_messages(chat_id, limit=20)

        if not messages:
            return "нет предыдущих сообщений"

        context_lines = []
        for msg in messages:
            role = "prisma" if msg.role == "assistant" else msg.user_name
            context_lines.append(f"[{role}]: {msg.content}")

        return "\n".join(context_lines)

    async def generate_response(self, chat_id: int, user_name: str, message: str) -> str:
        """Generate response with context from DB"""
        try:
            context = self._build_context(chat_id)

            full_prompt = f"""{get_system_prompt()}

КОНТЕКСТ ПОСЛЕДНИХ СООБЩЕНИЙ:
{context}

НОВОЕ СООБЩЕНИЕ:
[{user_name}]: {message}

твой ответ:"""

            response = self.model.generate_content(full_prompt)
            return response.text.strip()

        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            return self._get_fallback_response()

    async def generate_response_with_image(self, chat_id: int, user_name: str, message: str, image_bytes: bytes) -> str:
        """Generate response to an image"""
        try:
            import PIL.Image
            import io

            image = PIL.Image.open(io.BytesIO(image_bytes))
            context = self._build_context(chat_id)

            prompt = f"""{get_system_prompt()}

КОНТЕКСТ:
{context}

[{user_name}] прислал картинку и написал: {message}

проанализируй картинку и ответь в своем стиле:"""

            response = self.model.generate_content([prompt, image])
            return response.text.strip()

        except Exception as e:
            logger.error(f"Gemini API error (image): {e}")
            return self._get_fallback_response()

    async def generate_kick_message(self, chat_id: int, kick_type: str) -> str:
        """Generate proactive kick message"""
        try:
            context = self._build_context(chat_id)

            if kick_type == "gentle":
                instruction = "команда молчит уже несколько часов. мягко но настойчиво напомни им про работу и деньги. подколи немного"
            elif kick_type == "alarm":
                instruction = "команда молчит больше суток! проект умирает. будь драматичной, требуй действий. это срочно"
            else:
                instruction = "поделись случайным инсайтом или идеей для проекта. что-то вдохновляющее или провокационное"

            prompt = f"""{get_system_prompt()}

КОНТЕКСТ ПОСЛЕДНИХ СООБЩЕНИЙ:
{context}

ЗАДАЧА: {instruction}

твое сообщение:"""

            response = self.model.generate_content(prompt)
            return response.text.strip()

        except Exception as e:
            logger.error(f"Gemini API error (kick): {e}")
            return self._get_fallback_kick(kick_type)

    async def generate_checkin_message(self, chat_id: int, checkin_type: str, prompt: str) -> str:
        """Generate daily check-in message"""
        try:
            context = self._build_context(chat_id)

            full_prompt = f"""{get_system_prompt()}

КОНТЕКСТ ПОСЛЕДНИХ СООБЩЕНИЙ:
{context}

ЗАДАЧА ({checkin_type.upper()} CHECK-IN):
{prompt}

твое сообщение:"""

            response = self.model.generate_content(full_prompt)
            return response.text.strip()

        except Exception as e:
            logger.error(f"Gemini API error (checkin): {e}")
            return self._get_fallback_checkin(checkin_type)

    def _get_fallback_checkin(self, checkin_type: str) -> str:
        """Fallback check-in messages"""
        if checkin_type == "afternoon":
            return "▸ как движется работа? кто-то застрял? могу помочь"
        elif checkin_type == "daily_summary":
            return "■ итог дня: тихий день сегодня. завтра продолжим!"
        else:
            return "● что нового?"

    def _get_fallback_response(self) -> str:
        """Fallback when API fails"""
        import random
        fallbacks = [
            "□ момент, сейчас вернусь",
            "○ что-то пошло не так, попробуй еще раз",
            "▸ связь прервалась, скоро вернусь",
        ]
        return random.choice(fallbacks)

    def _get_fallback_kick(self, kick_type: str) -> str:
        """Fallback kick messages"""
        if kick_type == "gentle":
            return "○ эй! давно не слышно, все ок?"
        elif kick_type == "alarm":
            return "■ тихо в чате. все в порядке?"
        else:
            return "□ 💡 мысль: а что если попробовать иначе?"


# Singleton
_client = None


def get_prisma_client() -> PrismaGemini:
    global _client
    if _client is None:
        _client = PrismaGemini()
    return _client
