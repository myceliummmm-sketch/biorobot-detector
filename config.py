import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CALCULATOR_URL = os.getenv("CALCULATOR_URL", "https://cards.mycelium.gg/quiz")
MYCELIUM_APP_URL = os.getenv("MYCELIUM_APP_URL", "https://cards.mycelium.gg")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///mycelium_bot.db")

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")
SUPABASE_BRIDGE_URL = f"{SUPABASE_URL}/functions/v1/telegram-bot-bridge" if SUPABASE_URL else ""

# TMA (Telegram Mini App) for Vision Card
TMA_VISION_URL = os.getenv("TMA_VISION_URL", f"{MYCELIUM_APP_URL}/vision")

# Desktop Web App
DESKTOP_APP_URL = os.getenv("DESKTOP_APP_URL", "https://app.mycelium.gg")
