"""
Gemini client for Kuzya bot - warm family assistant
"""

import logging
import google.generativeai as genai
from config import GEMINI_API_KEY, SYSTEM_PROMPT
from database import get_recent_messages

logger = logging.getLogger(__name__)

# Configure Gemini
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)


class KuzyaClient:
    """Gemini client with Kuzya personality"""

    def __init__(self):
        self.model = genai.GenerativeModel(
            model_name="models/gemini-3-flash-preview",
            generation_config={
                "temperature": 0.7,
                "max_output_tokens": 1024,
            },
            system_instruction=SYSTEM_PROMPT
        )
        logger.info("KuzyaClient initialized")

    def _build_context(self, chat_id: int) -> str:
        """Build context from recent messages"""
        messages = get_recent_messages(chat_id, limit=30)

        if not messages:
            return "нет предыдущих сообщений"

        lines = []
        for msg in messages:
            role = msg["role"]
            name = msg["user_name"] or "?"
            content = msg["content"]

            if role == "user":
                lines.append(f"[{name}]: {content}")
            else:
                lines.append(f"[Кузя]: {content}")

        return "\n".join(lines[-30:])  # Last 30 messages

    async def generate_response(self, chat_id: int, user_name: str, message: str) -> str:
        """Generate response to user message"""
        try:
            context = self._build_context(chat_id)

            prompt = f"""{SYSTEM_PROMPT}

ИСТОРИЯ ЧАТА:
{context}

[{user_name}]: {message}

Ответь кратко и по делу:"""

            response = self.model.generate_content(prompt)

            return response.text.strip()

        except Exception as e:
            logger.error(f"Gemini error: {e}")
            return "Простите, что-то пошло не так. Попробуйте ещё раз?"

    async def generate_response_with_image(self, chat_id: int, user_name: str, caption: str, image_bytes: bytes) -> str:
        """Generate response to image"""
        try:
            import PIL.Image
            import io

            image = PIL.Image.open(io.BytesIO(image_bytes))

            prompt = f"{user_name} прислал фото"
            if caption:
                prompt += f" с подписью: {caption}"
            prompt += "\n\nОпиши что видишь и ответь на вопрос если есть."

            # Use sync version - works better with images
            response = self.model.generate_content([prompt, image])

            return response.text.strip()

        except Exception as e:
            logger.error(f"Image error: {e}")
            return "Не смог разобрать фотографию, простите."


# Singleton
_client = None


def get_kuzya_client() -> KuzyaClient:
    global _client
    if _client is None:
        _client = KuzyaClient()
    return _client
