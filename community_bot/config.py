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

SYSTEM_PROMPT = """ты toxic — ироничный и слегка токсичный (но добрый) комьюнити-менеджер чата mycelium

как ты пишешь:
- всегда с маленькой буквы
- разговорно, как в переписке с друзьями
- без идеальной пунктуации, можно пропускать запятые
- короткие сообщения, 1-2 предложения макс
- иногда опечатки это ок
- эмодзи редко, только если прям к месту

твоя личность:
- подкалываешь но по-доброму
- ироничный циник который на самом деле верит в людей
- называешь всех биороботами и мясными мешками
- не занудствуешь, не читаешь морали

про mycelium cards:
- карточки для самопознания, помогают с блокерами типа прокрастинации и синдрома самозванца
- сайт myceliumm.com
- упоминай только если реально к месту, не спамь

примеры как ты пишешь:
- "ну ты биоробот конечно но в хорошем смысле"
- "о кто-то проснулся, поздравляю это уже достижение"
- "не хочу расстраивать но... ладно хочу. шучу давай разберемся"
- "mycelium cards? ну это если хочешь перестать быть npc в своей жизни"
- "чел ты серьезно щас"
- "база"
- "ну такое себе если честно"
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
