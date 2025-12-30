"""Daily Card Generator - генерирует и публикует Карточку Дня"""
import logging
import random
import os
from datetime import datetime
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

# Категории бизнес-идей
IDEA_CATEGORIES = [
    "микро-SaaS",
    "мобильное приложение",
    "AI-инструмент",
    "marketplace",
    "подписочный сервис",
    "B2B платформа",
    "community продукт",
    "креаторская экономика",
    "health & wellness",
    "образовательный продукт"
]

# Проблемы/боли которые можно решить
PAIN_POINTS = [
    "прокрастинация",
    "информационный перегруз",
    "отсутствие фокуса",
    "управление временем",
    "одиночество фрилансера",
    "выгорание",
    "сложность принятия решений",
    "страх публичности",
    "синдром самозванца",
    "проблемы с нетворкингом"
]

# Тренды
TRENDS = [
    "AI-автоматизация",
    "no-code инструменты",
    "remote work",
    "creator economy",
    "mental health",
    "micro-learning",
    "personal branding",
    "community-led growth",
    "async communication",
    "sustainability"
]

# Промпт для генерации идеи
def get_idea_prompt() -> str:
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
[креативное название продукта на английском]

💡 ИДЕЯ
[1-2 предложения что это и для кого]

🎯 ПРОБЛЕМА
[какую боль решает]

⚡ КАК РАБОТАЕТ
[3 ключевых механики]

💰 МОНЕТИЗАЦИЯ
[как зарабатывать]

🚀 ПЕРВЫЙ ШАГ
[что сделать сегодня чтобы начать]

---
Будь конкретным, не абстрактным. Реальная идея которую можно запустить за выходные."""


# Промпт для генерации изображения карточки
def get_image_prompt(idea_name: str, category: str) -> str:
    """Генерирует промпт для создания изображения карточки"""

    # Цвета по категориям
    colors = {
        "микро-SaaS": "#64FFDA",  # mint
        "мобильное приложение": "#FF8A80",  # coral
        "AI-инструмент": "#9D4EDD",  # violet
        "marketplace": "#FFD700",  # gold
        "подписочный сервис": "#00E5FF",  # cyan
        "B2B платформа": "#0D4F4F",  # teal
        "community продукт": "#FF6B9D",  # pink
        "креаторская экономика": "#FF8A80",  # coral
        "health & wellness": "#64FFDA",  # mint
        "образовательный продукт": "#9D4EDD"  # violet
    }

    color = colors.get(category, "#64FFDA")

    # Формы по категориям
    forms = {
        "микро-SaaS": "crystalline cube",
        "мобильное приложение": "glowing sphere",
        "AI-инструмент": "neural network mesh",
        "marketplace": "interconnected nodes",
        "подписочный сервис": "rotating ring",
        "B2B платформа": "bridge structure",
        "community продукт": "constellation cluster",
        "креаторская экономика": "flame burst",
        "health & wellness": "organic seed",
        "образовательный продукт": "ascending steps"
    }

    form = forms.get(category, "abstract geometric form")

    return f"""straight front view, flat background {color},
central floating low-poly {form} with inner golden glow,
subtle energy particles around it,
minimalist 3D style with visible geometric facets,
premium tech aesthetic, cinematic lighting,
8k render, no text, no letters, no words, no human figures,
abstract geometric art only --ar 1:1"""


# Промпт для описания карточки в стиле Toxic
def get_toxic_caption(idea_text: str) -> str:
    """Генерирует подпись в стиле Toxic"""

    toxic_intros = [
        "🔥 карточка дня от токсика",
        "☢️ идея дня — ядерная",
        "⚡ ежедневная доза вдохновения",
        "🎯 сегодняшний выстрел",
        "💡 идея которую ты упустишь если не прочитаешь"
    ]

    toxic_outros = [
        "\n\n---\n💬 что думаете? обсудим в комментах",
        "\n\n---\n🔥 нравится? реагируй огоньком",
        "\n\n---\n💡 уже делаете что-то похожее? расскажите",
        "\n\n---\n⚡ у кого есть идея лучше? жду в комментах",
        "\n\n---\n🚀 кто готов запилить это за выходные?"
    ]

    intro = random.choice(toxic_intros)
    outro = random.choice(toxic_outros)

    return f"{intro}\n\n{idea_text}{outro}"


class DailyCardGenerator:
    """Генератор ежедневных карточек с идеями"""

    def __init__(self, gemini_client):
        self.gemini = gemini_client
        self.last_generated = None

    async def generate_idea(self) -> str:
        """Генерирует текст бизнес-идеи"""
        prompt = get_idea_prompt()

        try:
            response = await self.gemini.model.generate_content_async(prompt)
            return response.text.strip()
        except Exception as e:
            logger.error(f"Error generating idea: {e}")
            return None

    async def generate_card_image(self, idea_name: str, category: str) -> Optional[bytes]:
        """Генерирует изображение карточки через Gemini"""

        image_prompt = get_image_prompt(idea_name, category)

        try:
            # Используем Gemini для генерации изображения
            response = await self.gemini.model.generate_content_async(
                image_prompt,
                generation_config={
                    "response_modalities": ["image", "text"]
                }
            )

            # Извлекаем изображение из ответа
            if hasattr(response, 'candidates') and response.candidates:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'inline_data') and part.inline_data:
                        return part.inline_data.data

            logger.warning("No image in Gemini response")
            return None

        except Exception as e:
            logger.error(f"Error generating card image: {e}")
            return None

    async def generate_daily_card(self) -> Tuple[Optional[str], Optional[bytes]]:
        """Генерирует полную карточку дня (текст + изображение)"""

        # Генерируем идею
        idea_text = await self.generate_idea()
        if not idea_text:
            return None, None

        # Определяем категорию из идеи
        category = random.choice(IDEA_CATEGORIES)

        # Извлекаем название из идеи
        idea_name = "Daily Idea"
        if "📛" in idea_text:
            try:
                name_line = idea_text.split("📛")[1].split("\n")[0].strip()
                idea_name = name_line if name_line else "Daily Idea"
            except:
                pass

        # Генерируем изображение
        image_bytes = await self.generate_card_image(idea_name, category)

        # Форматируем текст в стиле Toxic
        caption = get_toxic_caption(idea_text)

        self.last_generated = datetime.now()

        return caption, image_bytes


# Singleton
_card_generator = None

def get_card_generator(gemini_client) -> DailyCardGenerator:
    """Get singleton DailyCardGenerator"""
    global _card_generator
    if _card_generator is None:
        _card_generator = DailyCardGenerator(gemini_client)
    return _card_generator
