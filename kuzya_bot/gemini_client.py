"""
Gemini client for Kuzya bot - warm family assistant
"""

import logging
import google.generativeai as genai
from config import GEMINI_API_KEY, SYSTEM_PROMPT

logger = logging.getLogger(__name__)

# Configure Gemini
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)


class KuzyaClient:
    """Gemini client with Kuzya personality"""

    def __init__(self):
        self.model = genai.GenerativeModel(
            model_name="models/gemini-2.0-flash",
            generation_config={
                "temperature": 0.7,
                "max_output_tokens": 1024,
            },
            system_instruction=SYSTEM_PROMPT
        )
        self.chat_histories = {}
        logger.info("KuzyaClient initialized")

    def _get_chat(self, chat_id: int):
        """Get or create chat session"""
        if chat_id not in self.chat_histories:
            self.chat_histories[chat_id] = self.model.start_chat(history=[])
        return self.chat_histories[chat_id]

    async def generate_response(self, chat_id: int, user_name: str, message: str) -> str:
        """Generate response to user message"""
        try:
            chat = self._get_chat(chat_id)

            prompt = f"{user_name}: {message}"
            response = await chat.send_message_async(prompt)

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

            response = await self.model.generate_content_async([prompt, image])

            return response.text.strip()

        except Exception as e:
            logger.error(f"Image error: {e}")
            return "Не смог разобрать фотографию, простите."

    def clear_history(self, chat_id: int):
        """Clear chat history"""
        if chat_id in self.chat_histories:
            del self.chat_histories[chat_id]


# Singleton
_client = None


def get_kuzya_client() -> KuzyaClient:
    global _client
    if _client is None:
        _client = KuzyaClient()
    return _client
