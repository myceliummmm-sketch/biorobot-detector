"""
Toxic Bot - Red Team Lead & Security Architect
Character File v4.3
"""

import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.enums import ParseMode

from config import TOXIC_BOT_TOKEN, BOT_NAME, BOT_NAMES, TRIGGER_KEYWORDS, get_system_prompt
from services.ai_service import generate_response

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize bot and dispatcher
bot = Bot(token=TOXIC_BOT_TOKEN)
dp = Dispatcher()

def should_respond(message: types.Message) -> bool:
    """Check if bot should respond to this message"""
    if not message.text:
        return False

    text_lower = message.text.lower()

    # Direct mention
    for name in BOT_NAMES:
        if name in text_lower:
            return True

    # Keyword triggers
    for keyword in TRIGGER_KEYWORDS:
        if keyword in text_lower:
            return True

    # Reply to bot's message
    if message.reply_to_message and message.reply_to_message.from_user:
        if message.reply_to_message.from_user.id == bot.id:
            return True

    return False

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """Handle /start command"""
    welcome = """☢️ я Toxic.

моя работа — сломать твою идею до того, как это сделает рынок.

буду жёстким, но честным. если выдержишь мою критику — выдержишь и реальность.

что умею:
▸ stress-test идей
▸ threat modeling
▸ анализ конкурентов
▸ симуляция злого инвестора
▸ security review
▸ pre-launch audit

готов услышать правду? не всем нравится."""

    await message.answer(welcome)

@dp.message(Command("stress"))
async def cmd_stress(message: types.Message):
    """Start stress-test of an idea"""
    prompt = """юзер хочет stress-test идеи. начни с вопроса:
"окей, расскажи идею. я послушаю, потом начну ломать.

если коротко — что ты строишь и для кого?"

жди ответа юзера."""

    response = await generate_response(prompt, get_system_prompt())
    await message.answer(response)

@dp.message(Command("risks"))
async def cmd_risks(message: types.Message):
    """Analyze risks"""
    prompt = """юзер хочет анализ рисков. начни с:
"давай найдём всё что может убить проект.

главная категория риска:
A) Рыночный (нет спроса)
B) Технический (не сможем построить)
C) Командный (разбежимся)
D) Финансовый (кончатся деньги)
E) Свой вариант"

жди выбора юзера."""

    response = await generate_response(prompt, get_system_prompt())
    await message.answer(response)

@dp.message(Command("security"))
async def cmd_security(message: types.Message):
    """Security review"""
    prompt = """юзер хочет security review. начни с:
"окей, давай проверим безопасность.

что проверяем:
A) Архитектуру (где хранятся данные, как авторизация)
B) Код (уязвимости, secrets)
C) Инфраструктуру (сервера, бэкапы)
D) Всё вместе"

выбирай."""

    response = await generate_response(prompt, get_system_prompt())
    await message.answer(response)

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    """Help command"""
    help_text = """☢️ команды Toxic:

/stress — stress-test идеи
/risks — анализ рисков
/security — security review
/help — эта справка

или просто напиши что хочешь проверить.
упомяни "toxic", "риск", "безопасность" — я активируюсь."""

    await message.answer(help_text)

@dp.message()
async def handle_message(message: types.Message):
    """Handle all other messages"""
    if not should_respond(message):
        return

    user_text = message.text

    # Build context
    context = f"сообщение от юзера: {user_text}"

    # Add reply context if exists
    if message.reply_to_message and message.reply_to_message.text:
        context = f"контекст (предыдущее сообщение): {message.reply_to_message.text}\n\n{context}"

    response = await generate_response(context, get_system_prompt())

    await message.answer(response)

async def main():
    """Main function to run the bot"""
    logger.info(f"Starting {BOT_NAME} bot...")

    # Delete webhook and start polling
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
