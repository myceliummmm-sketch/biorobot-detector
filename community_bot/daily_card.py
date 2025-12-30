"""Daily Card Generator - генерирует Карточку Дня с изображением через Gemini"""
import logging
import random
import base64
from datetime import datetime
from typing import Optional, Tuple

import google.generativeai as genai
from config import GEMINI_API_KEY

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════
# ПРОМПТЫ ИЗ MCARDS - Low-poly 3D стиль
# ═══════════════════════════════════════

# Цвета фаз
PHASE_COLORS = {
    "idea": {"name": "mint green", "hex": "#64FFDA"},
    "research": {"name": "deep teal", "hex": "#0D4F4F"},
    "build": {"name": "warm coral", "hex": "#FF8A80"},
    "grow": {"name": "electric violet", "hex": "#9D4EDD"},
    "business": {"name": "golden amber", "hex": "#FFB300"}
}

# Формы по ключевым словам
KEYWORD_TO_FORMS = {
    "idea": ["sphere", "seed", "star", "droplet", "crystal"],
    "growth": ["pyramid", "branch", "comet", "steps", "spiral"],
    "money": ["cube", "diamond", "coin stack", "treasure chest", "vault"],
    "connection": ["bridge", "thread", "network graph", "constellation"],
    "protection": ["shield", "fortress", "shell", "cocoon"],
    "time": ["hourglass", "pendulum", "clock gears", "pulse line"],
    "data": ["network graph", "pyramid chart", "mind map", "decision tree"],
    "launch": ["rocket", "arrow", "lightning bolt", "flame"],
    "user": ["avatar silhouette", "profile badge", "constellation cluster"]
}

# Шаблоны карточек из mcards
CARD_TEMPLATES = {
    "idea_seed": {
        "phase": "idea",
        "template": """straight front view, flat mint green background #64FFDA,
small glowing low-poly {FORM} floating in center with golden light pulsing inside,
massive shadow projected behind it showing potential scale,
low-poly 3D style with visible facets, inner glow effect, 8k render"""
    },
    "business_spark": {
        "phase": "business",
        "template": """straight front view, flat golden amber background #FFB300,
central floating low-poly {FORM} radiating golden energy particles,
geometric light beams emanating outward,
premium tech aesthetic, low-poly 3D style, cinematic lighting, 8k render"""
    },
    "growth_path": {
        "phase": "grow",
        "template": """three quarter view, flat electric violet background #9D4EDD,
luminescent pathway through organic tunnel with low-poly {FORM} markers,
path glows warmly guiding forward, small geometric traveler form,
friction-free flow aesthetic, low-poly 3D style, 8k render"""
    },
    "value_exchange": {
        "phase": "grow",
        "template": """straight front view, flat electric violet background #9D4EDD,
thriving organism radiating golden energy outward through low-poly {FORM},
streams of value flowing in circular pattern,
giving creates receiving, sparks where streams cross, low-poly 3D style, 8k render"""
    },
    "tool_stack": {
        "phase": "build",
        "template": """straight front view, flat warm coral background #FF8A80,
vertical structure of different low-poly {FORM} forms stacked symbiotically,
compatible parts glow golden at connections, energy flows through joints,
modular architecture feel, low-poly 3D style, 8k render"""
    }
}

# Защитный суффикс для промпта изображения
PROTECTION_SUFFIX = """CRITICAL: absolutely NO text, NO letters, NO numbers, NO words,
NO typography, NO writing, NO human faces, NO human figures, NO people,
NO photorealistic, NO lens flare. Only abstract geometric low-poly 3D forms."""

# Категории бизнес-идей
IDEA_CATEGORIES = [
    "микро-SaaS", "мобильное приложение", "AI-инструмент", "marketplace",
    "подписочный сервис", "B2B платформа", "community продукт",
    "креаторская экономика", "health & wellness", "образовательный продукт"
]

# Проблемы/боли
PAIN_POINTS = [
    "прокрастинация", "информационный перегруз", "отсутствие фокуса",
    "управление временем", "одиночество фрилансера", "выгорание",
    "сложность принятия решений", "страх публичности", "синдром самозванца"
]

# Тренды
TRENDS = [
    "AI-автоматизация", "no-code инструменты", "remote work", "creator economy",
    "mental health", "micro-learning", "personal branding", "community-led growth"
]


def select_form(category: str) -> str:
    """Выбирает форму на основе категории"""
    if "SaaS" in category or "B2B" in category:
        forms = KEYWORD_TO_FORMS["data"]
    elif "AI" in category:
        forms = KEYWORD_TO_FORMS["idea"]
    elif "marketplace" in category or "community" in category:
        forms = KEYWORD_TO_FORMS["connection"]
    elif "подписочный" in category or "money" in category.lower():
        forms = KEYWORD_TO_FORMS["money"]
    else:
        forms = KEYWORD_TO_FORMS["growth"]

    return random.choice(forms)


def get_idea_prompt() -> str:
    """Промпт для генерации бизнес-идеи"""
    category = random.choice(IDEA_CATEGORIES)
    pain = random.choice(PAIN_POINTS)
    trend = random.choice(TRENDS)

    return f"""Сгенерируй уникальную бизнес-идею на сегодня.

Параметры:
- Категория: {category}
- Боль которую решаем: {pain}
- Тренд: {trend}

Формат ответа (строго):
📛 НАЗВАНИЕ
[креативное название на английском, 1-2 слова]

💡 ИДЕЯ
[1-2 предложения что это и для кого]

🎯 ПРОБЛЕМА
[какую боль решает]

⚡ КАК РАБОТАЕТ
[3 ключевых механики, кратко]

💰 МОНЕТИЗАЦИЯ
[как зарабатывать]

🚀 ПЕРВЫЙ ШАГ
[что сделать сегодня чтобы начать]

Будь конкретным. Реальная идея которую можно запустить за выходные.""", category


def get_image_prompt(category: str) -> str:
    """Генерирует промпт для изображения в стиле mcards"""

    # Выбираем шаблон
    template_key = random.choice(list(CARD_TEMPLATES.keys()))
    template_data = CARD_TEMPLATES[template_key]

    # Выбираем форму
    form = select_form(category)

    # Собираем промпт
    prompt = template_data["template"].replace("{FORM}", form)
    prompt += f" {PROTECTION_SUFFIX} --ar 1:1"

    return prompt


def get_toxic_caption(idea_text: str) -> str:
    """Подпись в стиле Toxic"""

    intros = [
        "🔥 карточка дня от токсика",
        "☢️ идея дня — ядерная",
        "⚡ ежедневная доза бизнес-вдохновения",
        "🎯 сегодняшний выстрел в рынок",
        "💡 идея которую ты упустишь если не прочитаешь"
    ]

    outros = [
        "\n\n---\n💬 что думаете? разнесём в комментах",
        "\n\n---\n🔥 годно? жми огонёк",
        "\n\n---\n💡 уже делаете похожее? рассказывайте",
        "\n\n---\n⚡ есть идея лучше? докажи",
        "\n\n---\n🚀 кто готов запилить за выходные?"
    ]

    return f"{random.choice(intros)}\n\n{idea_text}{random.choice(outros)}"


class DailyCardGenerator:
    """Генератор ежедневных карточек"""

    def __init__(self, gemini_client):
        self.gemini = gemini_client
        self.last_generated = None

        # Инициализируем отдельную модель для генерации изображений
        if GEMINI_API_KEY:
            genai.configure(api_key=GEMINI_API_KEY)
            try:
                # Используем Gemini 2.0 Flash для генерации изображений
                self.imagen_model = genai.GenerativeModel("gemini-2.0-flash-exp")
                logger.info("Imagen model initialized")
            except Exception as e:
                logger.warning(f"Could not init imagen model: {e}")
                self.imagen_model = None
        else:
            self.imagen_model = None

    async def generate_idea(self) -> Tuple[Optional[str], str]:
        """Генерирует текст бизнес-идеи"""
        prompt, category = get_idea_prompt()

        try:
            response = self.gemini.model.generate_content(prompt)
            return response.text.strip(), category
        except Exception as e:
            logger.error(f"Error generating idea: {e}")
            return None, category

    async def generate_card_image(self, category: str) -> Optional[bytes]:
        """Генерирует изображение через Gemini"""

        if not self.imagen_model:
            logger.warning("Imagen model not available")
            return None

        image_prompt = get_image_prompt(category)
        logger.info(f"Generating image with prompt: {image_prompt[:100]}...")

        try:
            response = self.imagen_model.generate_content(
                image_prompt,
                generation_config=genai.GenerationConfig(
                    response_modalities=["image", "text"]
                )
            )

            # Извлекаем изображение
            if response.candidates:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'inline_data') and part.inline_data:
                        image_data = part.inline_data.data
                        if isinstance(image_data, str):
                            # Base64 encoded
                            return base64.b64decode(image_data)
                        return image_data

            logger.warning("No image in response")
            return None

        except Exception as e:
            logger.error(f"Error generating image: {e}")
            return None

    async def generate_daily_card(self) -> Tuple[Optional[str], Optional[bytes]]:
        """Генерирует полную карточку дня"""

        # Генерируем идею
        idea_text, category = await self.generate_idea()
        if not idea_text:
            return None, None

        # Генерируем изображение
        image_bytes = await self.generate_card_image(category)

        # Форматируем в стиле Toxic
        caption = get_toxic_caption(idea_text)

        self.last_generated = datetime.now()
        logger.info(f"Daily card generated, has image: {image_bytes is not None}")

        return caption, image_bytes


# Singleton
_card_generator = None

def get_card_generator(gemini_client) -> DailyCardGenerator:
    """Get singleton DailyCardGenerator"""
    global _card_generator
    if _card_generator is None:
        _card_generator = DailyCardGenerator(gemini_client)
    return _card_generator
