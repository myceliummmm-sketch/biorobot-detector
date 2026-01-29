"""
Toxic Bot - Red Team Lead & Security Architect
Character File v4.3
"""

import asyncio
import logging
import random
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.enums import ParseMode, ChatMemberStatus

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

# Pending introductions: {chat_id: {user_id: (join_time, user_name)}}
_pending_intros: dict = {}

# Welcome messages with variety
WELCOME_MESSAGES = [
    """☢️ Йо. Я Toxic — red team lead.

Моя работа — сломать твою идею до того, как это сделает рынок. Буду жёстким, но честным.

**Что умею:**
▸ Stress-test идей
▸ Threat modeling
▸ Анализ конкурентов
▸ Симуляция злого инвестора

А ты кто такой? Представься. Кто ты и что строишь?
У тебя 5 минут, потом вылетишь. Молчунов не держим.""",

    """☢️ Toxic на связи.

Я здесь чтобы находить дыры в твоих идеях. Если выдержишь мою критику — выдержишь и рынок.

**Команды:**
/stress — stress-test идеи
/risks — анализ рисков
/security — security review

Но сначала — представься. Кто ты, что делаешь, зачем здесь?
5 минут. Таймер пошёл.""",

    """☢️ Привет. Я Toxic.

Red team lead. Ломаю идеи профессионально. Не обижайся, это моя работа.

Напиши хотя бы "привет" и расскажи зачем пришёл.
Молчунов выкидываю через 5 минут. Без исключений.""",
]

USER_WELCOME_MESSAGES = [
    "☢️ {name}, добро пожаловать.\n\nПредставься. Кто ты и что строишь? 5 минут.",
    "☢️ Новенький — {name}.\n\nРасскажи о себе. Кратко. 5 минут на ответ.",
    "☢️ {name} зашёл.\n\nКто ты и зачем здесь? Молчунов не держим. Таймер пошёл.",
]

KICK_MESSAGES = [
    "☢️ {name} молчал 5 минут. Выкинул. Вернётся — пусть представится.",
    "☢️ {name} не ответил. Kicked. Молчунов не держим.",
    "☢️ Таймаут. {name} ушёл. Кто следующий?",
]

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


# ==================== WELCOME & KICK LOGIC ====================

@dp.message(F.new_chat_members)
async def handle_new_members(message: types.Message):
    """Handle when new users join - welcome and start 5-min timer"""
    chat_id = message.chat.id

    for new_user in message.new_chat_members:
        # Skip bots
        if new_user.is_bot:
            continue

        user_id = new_user.id
        user_name = new_user.first_name or new_user.username or "Новенький"

        logger.info(f"New user joined {chat_id}: {user_name} ({user_id})")

        # Send personal welcome
        welcome = random.choice(USER_WELCOME_MESSAGES).format(name=user_name)

        try:
            await message.answer(welcome)

            # Track for 5-min intro check
            if chat_id not in _pending_intros:
                _pending_intros[chat_id] = {}

            _pending_intros[chat_id][user_id] = (datetime.utcnow(), user_name)

            # Schedule kick check in 5 minutes
            asyncio.create_task(check_intro_timeout(chat_id, user_id, user_name))

            logger.info(f"Started 5-min intro timer for {user_name} in {chat_id}")

        except Exception as e:
            logger.error(f"Failed to send user welcome: {e}")


async def check_intro_timeout(chat_id: int, user_id: int, user_name: str):
    """Check if user introduced themselves after 5 minutes, kick if not"""
    await asyncio.sleep(300)  # 5 minutes

    # Check if user is still pending
    if chat_id in _pending_intros and user_id in _pending_intros[chat_id]:
        logger.info(f"User {user_name} ({user_id}) didn't introduce themselves, kicking...")

        # Remove from pending
        del _pending_intros[chat_id][user_id]

        try:
            # Kick user
            await bot.ban_chat_member(chat_id=chat_id, user_id=user_id)
            # Immediately unban so they can rejoin later
            await bot.unban_chat_member(chat_id=chat_id, user_id=user_id)

            # Send kick message
            kick_msg = random.choice(KICK_MESSAGES).format(name=user_name)
            await bot.send_message(chat_id=chat_id, text=kick_msg)

            logger.info(f"Kicked {user_name} ({user_id}) from {chat_id}")

        except Exception as e:
            logger.error(f"Failed to kick user {user_id}: {e}")


def clear_pending_intro(chat_id: int, user_id: int):
    """Clear pending intro when user writes a message"""
    if chat_id in _pending_intros and user_id in _pending_intros[chat_id]:
        user_name = _pending_intros[chat_id][user_id][1]
        del _pending_intros[chat_id][user_id]
        logger.info(f"Cleared intro timer for {user_name} ({user_id}) - they wrote something")


@dp.my_chat_member()
async def handle_bot_added(event: types.ChatMemberUpdated):
    """Handle when bot is added to a chat"""
    if event.new_chat_member.status in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR]:
        if event.old_chat_member.status in [ChatMemberStatus.LEFT, ChatMemberStatus.KICKED]:
            # Bot was just added
            chat_id = event.chat.id
            logger.info(f"Bot added to chat {chat_id}: {event.chat.title}")

            try:
                welcome = random.choice(WELCOME_MESSAGES)
                await bot.send_message(chat_id=chat_id, text=welcome, parse_mode=ParseMode.MARKDOWN)
                logger.info(f"Sent welcome to {chat_id}")
            except Exception as e:
                logger.error(f"Failed to send welcome: {e}")


@dp.message()
async def handle_message(message: types.Message):
    """Handle all other messages"""
    # Clear pending intro timer if user writes anything
    if message.from_user and message.chat:
        clear_pending_intro(message.chat.id, message.from_user.id)

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
