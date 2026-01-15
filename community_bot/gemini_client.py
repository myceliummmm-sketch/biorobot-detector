import logging
import random
from config import (
    GEMINI_API_KEY, SYSTEM_PROMPT,
    USE_VERTEX_AI, GCP_PROJECT_ID, GCP_LOCATION
)
from supabase_client import (
    get_workspace_by_chat_id,
    get_ai_history,
    save_ai_message,
    build_workspace_context,
    get_or_create_profile
)

logger = logging.getLogger(__name__)

# Random moods for variety
MOODS = [
    "сейчас ты в хорошем настроении, дружелюбный и поддерживающий",
    "сейчас ты немного саркастичный, подкалываешь но не зло",
    "сейчас ты в философском настроении, глубокие мысли",
    "сейчас ты энергичный и веселый",
    "сейчас ты чуть уставший и ленивый, отвечаешь коротко",
    "сейчас ты в критическом настроении, немного скептик",
    "сейчас ты максимально суппортивный и добрый",
    "сейчас ты в игривом настроении, шутишь",
]


class GeminiClient:
    def __init__(self):
        self.chat_histories = {}

        if USE_VERTEX_AI:
            self._init_vertex_ai()
        else:
            self._init_genai()

    def _init_genai(self):
        """Initialize with direct Gemini API key"""
        import google.generativeai as genai

        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is required")

        genai.configure(api_key=GEMINI_API_KEY)

        self.model = genai.GenerativeModel(
            model_name="models/gemini-3-flash-preview",
            system_instruction=SYSTEM_PROMPT,
            generation_config={
                "temperature": 0.9,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 1024,
            }
        )
        self.use_vertex = False
        logger.info("Initialized with Gemini API key")

    def _init_vertex_ai(self):
        """Initialize with Google Cloud Vertex AI"""
        import vertexai
        from vertexai.generative_models import GenerativeModel, GenerationConfig

        if not GCP_PROJECT_ID:
            raise ValueError("GCP_PROJECT_ID is required for Vertex AI")

        vertexai.init(project=GCP_PROJECT_ID, location=GCP_LOCATION)

        self.model = GenerativeModel(
            model_name="models/gemini-3-flash-preview",
            system_instruction=SYSTEM_PROMPT,
            generation_config=GenerationConfig(
                temperature=0.9,
                top_p=0.95,
                top_k=40,
                max_output_tokens=256,
            )
        )
        self.use_vertex = True
        logger.info(f"Initialized with Vertex AI (project: {GCP_PROJECT_ID})")

    def get_chat(self, chat_id: int):
        """Get or create chat session for a specific chat"""
        if chat_id not in self.chat_histories:
            self.chat_histories[chat_id] = self.model.start_chat(history=[])
        return self.chat_histories[chat_id]

    def _get_random_mood(self) -> str:
        """Get a random mood modifier"""
        return random.choice(MOODS)

    async def generate_response(self, chat_id: int, user_name: str, message: str, user_id: int = None) -> str:
        """Generate a response to a user message"""
        try:
            chat = self.get_chat(chat_id)
            mood = self._get_random_mood()

            # Get workspace context from Supabase
            workspace_context = build_workspace_context(chat_id)
            workspace = get_workspace_by_chat_id(chat_id)

            # Build prompt with context
            if workspace_context:
                prompt = f"{workspace_context}\n\n[настроение: {mood}]\n[{user_name}]: {message}"
            else:
                prompt = f"[настроение: {mood}]\n[{user_name}]: {message}"

            if self.use_vertex:
                response = await chat.send_message_async(prompt)
            else:
                response = chat.send_message(prompt)

            # Keep history manageable
            if len(chat.history) > 40:
                chat.history = chat.history[-40:]

            response_text = response.text.strip()

            # Save to Supabase if workspace exists
            if workspace and user_id:
                save_ai_message(workspace["id"], user_id, "toxic", "user", message)
                save_ai_message(workspace["id"], user_id, "toxic", "assistant", response_text)

            return response_text

        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            return self._get_fallback_response()

    async def generate_response_with_image(self, chat_id: int, user_name: str, message: str, image_bytes: bytes, user_id: int = None) -> str:
        """Generate a response to an image with optional text"""
        try:
            import PIL.Image
            import io

            # Convert bytes to PIL Image
            image = PIL.Image.open(io.BytesIO(image_bytes))

            # Get workspace context
            workspace_context = build_workspace_context(chat_id)
            workspace = get_workspace_by_chat_id(chat_id)

            prompt = f"{workspace_context}\n\n[{user_name}] прислал фото и написал: {message}" if workspace_context else f"[{user_name}] прислал фото и написал: {message}"

            # Generate response with image (use model directly, not chat for multimodal)
            response = self.model.generate_content([prompt, image])

            response_text = response.text.strip()

            # Save to Supabase if workspace exists
            if workspace and user_id:
                save_ai_message(workspace["id"], user_id, "toxic", "user", f"[ФОТО] {message}")
                save_ai_message(workspace["id"], user_id, "toxic", "assistant", response_text)

            return response_text

        except Exception as e:
            logger.error(f"Gemini API error (image): {e}")
            return self._get_fallback_response()

    def _get_fallback_response(self) -> str:
        """Fallback responses when API fails"""
        import random
        fallbacks = [
            "Мои нейроны временно в отпуске. Попробуй позже, биоробот",
            "Упс, мицелий в моей голове запутался. Дай мне секунду",
            "Сейчас не могу ответить, медитирую на грибницу",
            "Технические шоколадки... в смысле, неполадки. Скоро вернусь",
        ]
        return random.choice(fallbacks)

    def clear_history(self, chat_id: int):
        """Clear chat history for a specific chat"""
        if chat_id in self.chat_histories:
            del self.chat_histories[chat_id]


# Singleton instance
_client = None


def get_gemini_client() -> GeminiClient:
    global _client
    if _client is None:
        _client = GeminiClient()
    return _client
