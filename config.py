import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CALCULATOR_URL = os.getenv("CALCULATOR_URL", "https://cards.mycelium.gg/quiz")
MYCELIUM_APP_URL = os.getenv("MYCELIUM_APP_URL", "https://cards.mycelium.gg")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///mycelium_bot.db")
