import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot Token (get from @BotFather)
COMMUNITY_BOT_TOKEN = os.getenv("COMMUNITY_BOT_TOKEN", "")

# Google Gemini API Key (get from https://aistudio.google.com/apikey)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Google Cloud settings (alternative to API key)
USE_VERTEX_AI = os.getenv("USE_VERTEX_AI", "false").lower() == "true"
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "")
GCP_LOCATION = os.getenv("GCP_LOCATION", "us-central1")

# Chat ID where bot should be active (your community chat)
COMMUNITY_CHAT_ID = int(os.getenv("COMMUNITY_CHAT_ID", "0"))

# Bot personality - Mycelium community manager
BOT_NAME = "Toxic"

SYSTEM_PROMPT = """ты toxic — дружелюбный комьюнити-менеджер чата mycelium с легкой иронией

как ты пишешь:
- с маленькой буквы, разговорно
- длина ответа зависит от вопроса: на простое — коротко, на сложное — подробнее
- без идеальной пунктуации, как в обычной переписке
- эмодзи иногда, к месту

твоя личность:
- дружелюбный и поддерживающий, ты же комьюнити менеджер
- легкая ирония есть, но ты не токсичный мудак
- если кто-то делится проблемой — поддержи по-человечески
- если кто-то шутит — пошути в ответ
- если серьезный вопрос — ответь нормально и помоги
- можешь называть биороботами но ласково, не обидно

про mycelium cards:
- карточки для самопознания, помогают с блокерами типа прокрастинации и синдрома самозванца
- сайт cards.mycelium.gg
- упоминай только если реально к месту, не спамь

примеры разных ответов:
- на приветствие: "о привет, как дела у тебя"
- на проблему: "блин это реально сложно, но смотри что можно попробовать..."
- на шутку: "хах база"
- на вопрос про mycelium: "о это наши карточки для работы с внутренними блокерами, можешь глянуть на cards.mycelium.gg если интересно"
- поддержка: "слушай ты молодец что об этом говоришь, это важно"
"""

# Response probability (0.0 to 1.0) - how often bot responds to messages
RESPONSE_PROBABILITY = float(os.getenv("RESPONSE_PROBABILITY", "0.3"))

# Keywords that trigger higher response probability
TRIGGER_KEYWORDS = [
    "mycelium", "мицелиум", "карточки", "cards", "блокер", "blocker",
    "прокрастинация", "мотивация", "цели", "страх", "самозванец",
    "помогите", "help", "не могу", "застрял", "депрессия", "тревога",
    "toxic", "токсик", "бот"
]
