import logging
import json
import re
import google.generativeai as genai
from config import GEMINI_API_KEY, get_system_prompt
from database import get_recent_messages, get_memory_context, add_memory
from supabase_client import build_project_context, get_project_by_chat_id, save_ai_message

logger = logging.getLogger(__name__)

# YouTube-related keywords
YOUTUBE_KEYWORDS = [
    "youtube", "ютуб", "ютюб", "канал", "видео", "просмотр", "подписчик",
    "ролик", "views", "subscribers", "аналитика", "статистика канала"
]

# GitHub-related keywords
GITHUB_KEYWORDS = [
    "github", "гитхаб", "гит", "git", "коммит", "commit", "пулл реквест",
    "pull request", "pr", "мерж", "merge", "репо", "репозиторий", "код",
    "issue", "ишью", "бранч", "branch", "ветка", "деплой", "deploy"
]


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
        """Build context from recent messages, permanent memory, and project data"""
        # Get project context from Supabase (cards, project info)
        project_context = build_project_context(chat_id)

        # Get permanent memory
        memory_context = get_memory_context(chat_id, limit=15)

        # Get recent messages
        messages = get_recent_messages(chat_id, limit=50)

        if not messages:
            message_context = "нет предыдущих сообщений"
        else:
            context_lines = []
            for msg in messages:
                role = "prisma" if msg.role == "assistant" else msg.user_name
                context_lines.append(f"[{role}]: {msg.content}")
            message_context = "\n".join(context_lines)

        # Combine all context: project + memory + messages
        parts = []
        if project_context:
            parts.append(project_context)
        if memory_context:
            parts.append(memory_context)
        parts.append(f"=== ПОСЛЕДНИЕ СООБЩЕНИЯ ===\n{message_context}")

        return "\n\n".join(parts)

    def _check_youtube_context(self, message: str) -> str:
        """Check if message is about YouTube and return stats context if needed"""
        message_lower = message.lower()
        if any(kw in message_lower for kw in YOUTUBE_KEYWORDS):
            try:
                from youtube_client import get_youtube_client
                yt = get_youtube_client()
                if yt.is_available():
                    stats = yt.get_channel_stats()
                    analytics = yt.get_analytics_last_days(7)
                    videos = yt.get_recent_videos(3)

                    lines = ["\n=== ДАННЫЕ YOUTUBE (используй для ответа) ==="]
                    if stats:
                        lines.append(f"Канал: {stats['title']}")
                        lines.append(f"Подписчиков: {stats['subscribers']:,}")
                        lines.append(f"Всего просмотров: {stats['total_views']:,}")
                    if analytics:
                        lines.append(f"За 7 дней: {analytics['views']:,} просмотров, {analytics['subs_net']:+d} подписчиков")
                    if videos:
                        lines.append("Последние видео:")
                        for v in videos:
                            lines.append(f"  - {v['title']}: {v['views']:,} просмотров")
                    return "\n".join(lines)
            except Exception as e:
                logger.debug(f"YouTube context error: {e}")
        return ""

    def _check_github_context(self, message: str) -> str:
        """Check if message is about GitHub and return repo context if needed"""
        message_lower = message.lower()
        if any(kw in message_lower for kw in GITHUB_KEYWORDS):
            try:
                from github_client import get_github_client
                gh = get_github_client()
                if gh.is_available():
                    summary = gh.get_full_summary()
                    return f"\n\n=== ДАННЫЕ GITHUB (используй для ответа) ===\n{summary}"
            except Exception as e:
                logger.debug(f"GitHub context error: {e}")
        return ""

    async def generate_response(self, chat_id: int, user_name: str, message: str, user_id: int = None) -> str:
        """Generate response with context from DB"""
        try:
            context = self._build_context(chat_id)

            # Add smart context if message is about specific topics
            youtube_context = self._check_youtube_context(message)
            github_context = self._check_github_context(message)

            full_prompt = f"""{get_system_prompt()}

КОНТЕКСТ ПОСЛЕДНИХ СООБЩЕНИЙ:
{context}{youtube_context}{github_context}

НОВОЕ СООБЩЕНИЕ:
[{user_name}]: {message}

твой ответ:"""

            response = self.model.generate_content(full_prompt)
            response_text = response.text.strip()

            # Save to Supabase if project exists
            project = get_project_by_chat_id(chat_id)
            if project and user_id:
                save_ai_message(project["id"], user_id, "prisma", "user", message)
                save_ai_message(project["id"], user_id, "prisma", "assistant", response_text)

            # Try to auto-save important info (fire and forget)
            try:
                await self._analyze_and_save_memory(chat_id, user_name, message)
            except Exception as e:
                logger.debug(f"Memory save skipped: {e}")

            return response_text

        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            return self._get_fallback_response()

    async def _analyze_and_save_memory(self, chat_id: int, user_name: str, message: str):
        """Analyze message and save important info to permanent memory"""
        # Skip short messages
        if len(message) < 20:
            return

        analysis_prompt = f"""Проанализируй это сообщение от {user_name}:
"{message}"

Определи, содержит ли оно ВАЖНУЮ информацию для проекта, которую стоит запомнить навсегда.

Категории для сохранения:
- decision: принятое решение по проекту
- task: новая задача или взятое обязательство
- insight: ценная идея или инсайт
- fact: важный факт о проекте/команде/продукте
- blocker: блокер или проблема
- progress: значимый прогресс или достижение

Если сообщение НЕ содержит важной информации (обычная болтовня, вопрос, короткий ответ) — верни пустой JSON: {{}}

Если содержит — верни JSON:
{{"category": "категория", "content": "краткое описание на русском, 1-2 предложения"}}

ТОЛЬКО JSON, без пояснений:"""

        try:
            response = self.model.generate_content(analysis_prompt)
            text = response.text.strip()

            # Clean up response
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            text = text.strip()

            if not text or text == "{}":
                return

            data = json.loads(text)
            if data and "category" in data and "content" in data:
                add_memory(
                    chat_id=chat_id,
                    category=data["category"],
                    content=data["content"],
                    added_by=user_name
                )
                logger.info(f"Auto-saved memory: [{data['category']}] {data['content'][:50]}...")

        except json.JSONDecodeError:
            pass  # Not valid JSON, skip
        except Exception as e:
            logger.debug(f"Memory analysis failed: {e}")

    async def generate_response_with_image(self, chat_id: int, user_name: str, message: str, image_bytes: bytes, user_id: int = None) -> str:
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
            response_text = response.text.strip()

            # Save to Supabase if project exists
            project = get_project_by_chat_id(chat_id)
            if project and user_id:
                save_ai_message(project["id"], user_id, "prisma", "user", f"[ФОТО] {message}")
                save_ai_message(project["id"], user_id, "prisma", "assistant", response_text)

            return response_text

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
