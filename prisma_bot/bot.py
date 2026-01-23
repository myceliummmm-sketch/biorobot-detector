import logging
import random
import asyncio
from datetime import datetime, time
from telegram import Update, InlineKeyboardMarkup, ChatMemberUpdated
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ChatMemberHandler, filters, ContextTypes

try:
    import pytz
    PYTZ_AVAILABLE = True
except ImportError:
    PYTZ_AVAILABLE = False

from config import (
    PRISMA_BOT_TOKEN,
    BOT_NAME,
    BOT_NAMES,
    TRIGGER_KEYWORDS,
    SILENCE_KICK_HOURS,
    SILENCE_ALARM_HOURS,
    RANDOM_INSIGHT_CHANCE,
    PROACTIVE_CHECK_MINUTES,
    TIMEZONE,
    DAILY_CHECKINS,
    CHECKIN_PROMPTS,
    GOOGLE_DOCS_FOLDER_ID,
    ADMIN_USERNAME
)
from database import (
    init_db,
    log_message,
    update_last_message_time,
    get_silence_duration,
    update_last_kick_time,
    get_all_active_chats,
    get_today_messages,
    get_all_memories,
    add_memory,
    delete_memory,
    is_chat_muted,
    set_chat_muted
)
from gemini_client import get_prisma_client
from google_docs_client import get_docs_client
from github_client import get_github_client
from youtube_client import get_youtube_client
from services.dialog_engine import get_dialog_engine
from supabase_client import get_supabase

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


# ==================== TOPIC DETECTION ====================

# Topic names that Prisma recognizes (case-insensitive)
TOPIC_MAPPING = {
    "idea": "idea_thread_id",
    "идея": "idea_thread_id",
    "#idea": "idea_thread_id",
    "#идея": "idea_thread_id",
    "research": "research_thread_id",
    "рисерч": "research_thread_id",
    "#research": "research_thread_id",
    "build": "build_thread_id",
    "билд": "build_thread_id",
    "#build": "build_thread_id",
    "grow": "grow_thread_id",
    "гроу": "grow_thread_id",
    "#grow": "grow_thread_id",
    "general": "general_thread_id",
    "#general": "general_thread_id",
}


async def detect_topic_by_name(context: ContextTypes.DEFAULT_TYPE, chat_id: int, thread_id: int) -> str:
    """
    Detect topic type by fetching forum topic name.
    Returns: topic type key (idea/research/build/grow/general) or None
    """
    if not thread_id:
        return None

    try:
        # Try to get topic info - Note: this may not work in all cases
        # Telegram Bot API doesn't provide direct forum topic info
        # We rely on the stored mapping in database
        return None
    except Exception as e:
        logger.debug(f"Could not detect topic name: {e}")
        return None


def is_idea_topic_by_name(topic_name: str) -> bool:
    """Check if topic name indicates it's an #idea topic"""
    if not topic_name:
        return False
    name_lower = topic_name.lower().strip()
    return name_lower in ["idea", "идея", "#idea", "#идея", "💡 idea", "💡 идея"]


# ==================== WELCOME MESSAGE ====================

WELCOME_MESSAGE = """💎 Привет! Я Prisma — твой продакт-менеджер.

Моя работа — помочь тебе понять, что ты строишь и для кого. Буду вести через карточки, задавать вопросы и держать фокус на важном.

📍 **Как работаем:**
▸ Пиши в топик **#idea** — там я проведу тебя через 5 карточек
▸ Можешь отвечать голосом — я расшифрую
▸ На каждый вопрос предложу варианты A/B/C/D

🎴 **Фаза IDEA — 5 карт:**
1. 🎯 Продукт — что создаёшь?
2. 🔥 Проблема — чью боль решаешь?
3. 👥 Аудитория — кто твой человек?
4. 💎 Ценность — в чём выгода?
5. 🔮 Видение — куда это ведёт?

Готов? Напиши что-нибудь в **#idea** и начнём! 💎"""


async def handle_new_chat_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle when bot is added to a chat - send welcome to #General if topics enabled"""
    chat_member = update.my_chat_member
    if not chat_member:
        return

    new_member = chat_member.new_chat_member
    old_member = chat_member.old_chat_member

    # Check if the bot was added (status changed from restricted/left/kicked to member/admin)
    was_not_member = old_member.status in ["left", "kicked", "restricted"]
    is_now_member = new_member.status in ["member", "administrator"]

    if not (was_not_member and is_now_member):
        return

    chat = chat_member.chat
    chat_id = chat.id

    logger.info(f"Bot added to chat {chat_id}: {chat.title}")

    # Check if it's a supergroup with topics
    if chat.type == "supergroup":
        try:
            # Try to send welcome to the main chat (General topic has thread_id = None or 0)
            await context.bot.send_message(
                chat_id=chat_id,
                text=WELCOME_MESSAGE,
                parse_mode="Markdown"
            )
            logger.info(f"Sent welcome message to {chat_id}")
        except Exception as e:
            logger.error(f"Failed to send welcome: {e}")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all incoming messages - log and maybe respond"""
    message = update.message
    if not message or not message.text:
        return

    chat_id = message.chat_id
    user = message.from_user
    thread_id = message.message_thread_id

    # Skip bots
    if user.is_bot:
        return

    user_name = user.first_name or user.username or "аноним"

    # === DIALOG ENGINE ROUTING ===
    # Check if this message is in an #idea topic that DialogEngine should handle
    if thread_id:
        try:
            supabase = get_supabase()
            if supabase:
                engine = get_dialog_engine(supabase)
                project_id = engine.get_project_by_chat(chat_id)

                if project_id and engine.should_handle_message(project_id, thread_id):
                    # DialogEngine handles this message
                    logger.info(f"DialogEngine handling message in #idea topic")

                    response, keyboard_data = engine.process_message(
                        project_id=project_id,
                        user_message=message.text,
                        user_name=user_name
                    )

                    reply_markup = None
                    if keyboard_data:
                        reply_markup = InlineKeyboardMarkup(keyboard_data["inline_keyboard"])

                    await message.reply_text(
                        response,
                        parse_mode="Markdown",
                        reply_markup=reply_markup
                    )
                    return  # DialogEngine handled it, stop here

        except Exception as e:
            logger.error(f"DialogEngine error: {e}")
            # Continue with normal handling if DialogEngine fails

    # Log message to DB
    log_message(chat_id, user.id, user_name, "user", message.text)
    update_last_message_time(chat_id)

    logger.info(f"Message from {user_name}: {message.text[:50]}...")

    # Check if bot should respond
    bot_username = (await context.bot.get_me()).username
    text_lower = message.text.lower()

    is_reply_to_bot = (
        message.reply_to_message and
        message.reply_to_message.from_user and
        message.reply_to_message.from_user.id == context.bot.id
    )
    is_mention = f"@{bot_username}" in message.text if bot_username else False
    is_called = any(name in text_lower for name in BOT_NAMES)
    has_keyword = any(keyword in text_lower for keyword in TRIGGER_KEYWORDS)

    # Always respond to direct calls, mentions, replies
    # 30% chance to respond to keywords
    if is_reply_to_bot or is_mention or is_called:
        pass  # Respond
    elif has_keyword and random.random() < 0.3:
        pass  # 30% chance on keywords
    else:
        return

    logger.info(f"Responding to {user_name}")

    # Show typing
    await context.bot.send_chat_action(chat_id=chat_id, action="typing")
    await asyncio.sleep(random.uniform(1.0, 2.0))

    try:
        prisma = get_prisma_client()
        response = await prisma.generate_response(chat_id, user_name, message.text, user_id=user.id)

        # Log bot response
        log_message(chat_id, 0, "Prisma", "assistant", response)

        await message.reply_text(response)
        logger.info(f"Sent response: {response[:50]}...")

    except Exception as e:
        logger.error(f"Error: {e}")


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle voice messages - transcribe with Whisper and respond"""
    message = update.message
    if not message or not message.voice:
        return

    chat_id = message.chat_id
    user = message.from_user

    if user.is_bot:
        return

    user_name = user.first_name or user.username or "аноним"
    duration = message.voice.duration or 0

    logger.info(f"Voice message from {user_name}, duration: {duration}s")

    import os as os_module

    # Warn if very long
    if duration > 300:
        await message.reply_text("● длинное голосовое, расшифровываю... подожди минутку")
    elif duration > 60:
        await message.reply_text("● расшифровываю голосовое...")

    try:
        # Download voice file
        voice = message.voice
        file = await context.bot.get_file(voice.file_id)
        voice_path = f"/tmp/voice_{voice.file_id}.ogg"
        await file.download_to_drive(voice_path)
        logger.info(f"Voice downloaded: {voice_path}, duration: {voice.duration}s")

        # Limit duration (5 min max to avoid long processing)
        if voice.duration > 300:
            await message.reply_text("○ аудио слишком длинное (макс 5 мин). разбей на части )")
            if os_module.path.exists(voice_path):
                os_module.unlink(voice_path)
            return

        text = None
        error_msg = None

        # Try OpenAI Whisper API first (fast!)
        openai_key = os_module.environ.get("OPENAI_API_KEY")
        if openai_key:
            try:
                import requests
                logger.info("Trying OpenAI Whisper API...")

                with open(voice_path, "rb") as audio_file:
                    response = requests.post(
                        "https://api.openai.com/v1/audio/transcriptions",
                        headers={"Authorization": f"Bearer {openai_key}"},
                        files={"file": audio_file},
                        data={"model": "whisper-1", "language": "ru"},
                        timeout=60
                    )

                if response.ok:
                    text = response.json().get("text", "").strip()
                    logger.info(f"OpenAI Whisper OK: {text[:50]}...")
                else:
                    error_msg = f"OpenAI API: {response.status_code}"
                    logger.warning(error_msg)
            except Exception as e:
                error_msg = f"OpenAI: {str(e)[:50]}"
                logger.warning(error_msg)

        # Fallback to Google Speech (for short audio only)
        if not text:
            try:
                import subprocess
                import speech_recognition as sr
                logger.info("Trying Google Speech...")

                wav_path = f"/tmp/voice_{voice.file_id}.wav"
                result = subprocess.run(
                    ["ffmpeg", "-y", "-i", voice_path, "-ar", "16000", "-ac", "1", wav_path],
                    capture_output=True,
                    timeout=30
                )

                if result.returncode != 0:
                    error_msg = "ffmpeg не работает"
                    logger.error(f"ffmpeg error: {result.stderr.decode()[:100]}")
                else:
                    recognizer = sr.Recognizer()
                    with sr.AudioFile(wav_path) as source:
                        audio = recognizer.record(source)
                    text = recognizer.recognize_google(audio, language="ru-RU")
                    logger.info(f"Google Speech OK: {text[:50]}...")

                if os_module.path.exists(wav_path):
                    os_module.unlink(wav_path)

            except ImportError:
                error_msg = "SpeechRecognition не установлен"
                logger.error(error_msg)
            except Exception as e:
                error_msg = f"Speech: {str(e)[:50]}"
                logger.error(error_msg)

        # Clean up
        if os_module.path.exists(voice_path):
            os_module.unlink(voice_path)

        if not text:
            await message.reply_text(f"○ не смогла расшифровать: {error_msg or 'неизвестная ошибка'}")
            return

        # Log and respond
        log_message(chat_id, user.id, user_name, "user", f"[голосовое] {text}")
        update_last_message_time(chat_id)

        await context.bot.send_chat_action(chat_id=chat_id, action="typing")

        prisma = get_prisma_client()
        response = await prisma.generate_response(chat_id, user_name, text, user_id=user.id)

        log_message(chat_id, 0, "Prisma", "assistant", response)

        transcription_preview = text[:500] + "..." if len(text) > 500 else text
        await message.reply_text(f"🎤 \"{transcription_preview}\"\n\n{response}")

    except Exception as e:
        logger.error(f"Voice error: {e}")
        await message.reply_text(f"○ ошибка: {str(e)[:100]}")


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle photos"""
    message = update.message
    if not message or not message.photo:
        return

    chat_id = message.chat_id
    user = message.from_user

    if user.is_bot:
        return

    user_name = user.first_name or user.username or "аноним"
    caption = message.caption or ""

    # Log
    log_message(chat_id, user.id, user_name, "user", f"[ФОТО] {caption}")
    update_last_message_time(chat_id)

    # Check if should respond
    bot_username = (await context.bot.get_me()).username
    caption_lower = caption.lower()

    is_reply_to_bot = (
        message.reply_to_message and
        message.reply_to_message.from_user and
        message.reply_to_message.from_user.id == context.bot.id
    )
    is_mention = f"@{bot_username}" in caption if bot_username else False
    is_called = any(name in caption_lower for name in BOT_NAMES)

    if not (is_reply_to_bot or is_mention or is_called):
        return

    logger.info(f"Processing photo from {user_name}")

    await context.bot.send_chat_action(chat_id=chat_id, action="typing")

    try:
        photo = message.photo[-1]
        file = await context.bot.get_file(photo.file_id)
        photo_bytes = await file.download_as_bytearray()

        prisma = get_prisma_client()
        response = await prisma.generate_response_with_image(
            chat_id, user_name, caption or "что думаешь?", bytes(photo_bytes), user_id=user.id
        )

        log_message(chat_id, 0, "Prisma", "assistant", response)
        await message.reply_text(response)

    except Exception as e:
        logger.error(f"Error processing photo: {e}")


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start"""
    await update.message.reply_text(
        "○ привет! я prisma — ai операционщица mycelium.\n\n"
        "помогаю с прогрессом и держу фокус. тегни когда нужен совет ▸"
    )


async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /balance - Show user's Spores balance and earning rules (UC-50)"""
    from supabase_client import get_user_balance, get_or_create_profile

    user = update.effective_user
    telegram_id = user.id
    user_name = user.first_name or user.username or "stranger"

    # Ensure profile exists
    get_or_create_profile(telegram_id, user.username, user_name)

    # Get balance
    balance_data = get_user_balance(telegram_id)

    spores = balance_data.get("spores_balance", 0)
    xp = balance_data.get("xp", 0)

    # Format response with economy rules
    response = f"""🍄 **Spores Balance**

**{user_name}**, твой баланс:
▸ 🌿 Spores: **{spores}**
▸ ⚡ XP: **{xp}**

━━━━━━━━━━━━━━━━━━━━

💰 **Как заработать:**
• Epic Card → +10 Spores
• Legendary Card → +25 Spores
• Phase Completion → +20 Spores

💸 **Расходы:**
• Reforge (исправление) → -10 Spores
• Auto-fill ("I don't know") → -10 Spores

━━━━━━━━━━━━━━━━━━━━
_Evaluate → Forge → Earn_"""

    await update.message.reply_text(response, parse_mode="Markdown")


async def startidea_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /startidea - Start the IDEA phase questionnaire"""
    message = update.message
    chat_id = message.chat_id

    supabase = get_supabase()
    if not supabase:
        await message.reply_text("❌ База данных не подключена.")
        return

    engine = get_dialog_engine(supabase)

    # Get project
    project_id = engine.get_project_by_chat(chat_id)
    if not project_id:
        await message.reply_text(
            "❌ Проект не найден.\n\n"
            "Сначала создай воркспейс через веб-приложение и привяжи к этому чату."
        )
        return

    # Start dialog
    success, first_question = engine.start_dialog(project_id)

    if success:
        await message.reply_text(
            f"🚀 **Запускаем фазу IDEA!**\n\n"
            f"Сейчас заполним 5 карточек:\n"
            f"1. 🎯 Product\n"
            f"2. 🔥 Problem\n"
            f"3. 👥 Audience\n"
            f"4. 💎 Value\n"
            f"5. 🚀 Vision\n\n"
            f"Пиши ответы в топик **#idea**!\n\n{first_question}",
            parse_mode="Markdown"
        )
    else:
        await message.reply_text("❌ Ошибка при запуске. Попробуй позже.")


async def ideaprogress_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /ideaprogress - Show current progress in IDEA phase"""
    message = update.message
    chat_id = message.chat_id

    supabase = get_supabase()
    if not supabase:
        await message.reply_text("❌ База данных не подключена.")
        return

    engine = get_dialog_engine(supabase)
    project_id = engine.get_project_by_chat(chat_id)

    if not project_id:
        await message.reply_text("❌ Проект не найден.")
        return

    progress = engine.get_progress(project_id)

    if not progress.get("started"):
        await message.reply_text(
            "Фаза IDEA ещё не начата.\n\n"
            "Используй /startidea чтобы начать."
        )
        return

    cards_done = progress["cards_completed"]
    current = progress["current_card"].title()
    question = progress["current_question"]
    percent = progress["progress_percent"]

    bar = "●" * cards_done + "○" * (5 - cards_done)

    await message.reply_text(
        f"📊 **Прогресс IDEA**\n\n"
        f"[{bar}] {cards_done}/5 карт\n\n"
        f"Текущая карта: **{current}**\n"
        f"Вопрос: {question}/5\n\n"
        f"Общий прогресс: {percent}%",
        parse_mode="Markdown"
    )


async def handle_dialog_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle callback button presses from DialogEngine"""
    query = update.callback_query
    if not query or not query.data:
        return

    data = query.data

    # Check if this is a dialog callback
    if not data.startswith(("confirm_card:", "redo_card:")):
        return

    await query.answer()

    supabase = get_supabase()
    if not supabase:
        await query.edit_message_text("❌ База данных не подключена.")
        return

    engine = get_dialog_engine(supabase)

    if data.startswith("confirm_card:"):
        project_id = data.split(":")[1]
        response, keyboard_data = engine.confirm_card(project_id)

    elif data.startswith("redo_card:"):
        project_id = data.split(":")[1]
        response, keyboard_data = engine.redo_card(project_id)

    else:
        return

    # Edit message with response
    reply_markup = None
    if keyboard_data:
        reply_markup = InlineKeyboardMarkup(keyboard_data["inline_keyboard"])

    await query.edit_message_text(
        response,
        parse_mode="Markdown",
        reply_markup=reply_markup
    )


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /status"""
    chat_id = update.message.chat_id
    silence = get_silence_duration(chat_id)

    status = "активен ✨" if silence < SILENCE_KICK_HOURS else "притих 💤" if silence < SILENCE_ALARM_HOURS else "тихо ⚡"

    # Get GitHub status
    github = get_github_client()
    github_status = ""
    if github.is_available():
        commits = github.get_today_commits()
        github_status = f"\n● GitHub: {len(commits)} коммитов сегодня"

    await update.message.reply_text(
        f"▸ статус: {status}\n"
        f"○ тишина: {silence:.1f}ч{github_status}"
    )


async def prompt_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /prompt - only for admin"""
    user = update.message.from_user
    username = user.username or ""

    # Check if user is admin
    if username.lower() != ADMIN_USERNAME.lower():
        await update.message.reply_text("○ эта команда только для Артема")
        return

    # Get the prompt text
    if not context.args:
        await update.message.reply_text(
            "▸ использование:\n"
            "/prompt добавить [текст] — добавить в промпт\n"
            "/prompt показать — показать текущие дополнения"
        )
        return

    action = context.args[0].lower()
    text = " ".join(context.args[1:]) if len(context.args) > 1 else ""

    if action == "показать":
        # TODO: read from DB
        await update.message.reply_text("○ дополнений к промпту пока нет")
    elif action == "добавить" and text:
        # TODO: save to DB
        await update.message.reply_text(f"● добавлено в промпт:\n{text}")
        logger.info(f"Admin {username} added to prompt: {text}")
    else:
        await update.message.reply_text("○ не понял команду. /prompt для справки")


async def memory_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /memory - view and manage permanent memory"""
    user = update.message.from_user
    username = user.username or ""
    chat_id = update.message.chat_id

    # Check if user is admin
    if username.lower() != ADMIN_USERNAME.lower():
        await update.message.reply_text("○ эта команда только для Артема")
        return

    if not context.args:
        await update.message.reply_text(
            "▸ постоянная память prisma\n\n"
            "/memory показать — все записи\n"
            "/memory добавить [категория] [текст]\n"
            "/memory удалить [id]\n\n"
            "категории: decision, task, insight, fact, blocker, progress"
        )
        return

    action = context.args[0].lower()

    if action == "показать":
        memories = get_all_memories(chat_id)
        if not memories:
            await update.message.reply_text("○ память пуста")
            return

        lines = ["■ постоянная память:\n"]
        for m in memories[:20]:  # Limit to 20
            lines.append(f"#{m.id} [{m.category}] {m.content[:100]}")
            lines.append(f"   добавил: {m.added_by}\n")

        await update.message.reply_text("\n".join(lines))

    elif action == "добавить" and len(context.args) >= 3:
        category = context.args[1].lower()
        content = " ".join(context.args[2:])

        valid_categories = ["decision", "task", "insight", "fact", "blocker", "progress"]
        if category not in valid_categories:
            await update.message.reply_text(f"○ неизвестная категория. доступные: {', '.join(valid_categories)}")
            return

        if add_memory(chat_id, category, content, username):
            await update.message.reply_text(f"● добавлено в память [{category}]:\n{content}")
        else:
            await update.message.reply_text("○ ошибка сохранения")

    elif action == "удалить" and len(context.args) >= 2:
        try:
            memory_id = int(context.args[1])
            if delete_memory(memory_id):
                await update.message.reply_text(f"● запись #{memory_id} удалена")
            else:
                await update.message.reply_text("○ ошибка удаления")
        except ValueError:
            await update.message.reply_text("○ укажи ID записи числом")

    else:
        await update.message.reply_text("○ не понял команду. /memory для справки")


async def youtube_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /youtube - show YouTube channel stats (admin only)"""
    user = update.message.from_user
    username = user.username or ""

    # Only admin can see detailed stats
    if username.lower() != ADMIN_USERNAME.lower():
        await update.message.reply_text("○ детальная статистика YouTube только для Артема. но можешь спросить меня про канал — отвечу )")
        return

    yt = get_youtube_client()

    if not yt.is_available():
        await update.message.reply_text("○ YouTube не подключен. нужен YOUTUBE_REFRESH_TOKEN")
        return

    # Get channel stats
    stats = yt.get_channel_stats()
    if not stats:
        await update.message.reply_text("○ не удалось получить статистику")
        return

    lines = [f"📺 {stats['title']}", ""]
    lines.append(f"▸ подписчиков: {stats['subscribers']:,}")
    lines.append(f"▸ всего просмотров: {stats['total_views']:,}")
    lines.append(f"▸ видео: {stats['video_count']}")

    # Weekly analytics
    analytics = yt.get_analytics_last_days(7)
    if analytics:
        lines.append("")
        lines.append("■ за последние 7 дней:")
        lines.append(f"  просмотров: {analytics['views']:,}")
        lines.append(f"  часов просмотра: {analytics['watch_hours']}")
        if analytics['subs_net'] >= 0:
            lines.append(f"  подписчиков: +{analytics['subs_net']}")
        else:
            lines.append(f"  подписчиков: {analytics['subs_net']}")

    # Recent videos
    videos = yt.get_recent_videos(3)
    if videos:
        lines.append("")
        lines.append("● последние видео:")
        for v in videos:
            lines.append(f"  {v['title']}")
            lines.append(f"    {v['views']:,} 👁  {v['likes']} ❤️")

    await update.message.reply_text("\n".join(lines))


async def upload_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /upload - upload video to YouTube with AI-generated description"""
    user = update.message.from_user
    username = user.username or ""
    chat_id = update.message.chat_id

    # Check if user is admin
    if username.lower() != ADMIN_USERNAME.lower():
        await update.message.reply_text("○ загрузка только для Артема")
        return

    yt = get_youtube_client()
    if not yt.is_available():
        await update.message.reply_text("○ YouTube не подключен")
        return

    # Get title from command args
    if not context.args:
        await update.message.reply_text(
            "▸ как использовать:\n\n"
            "1. отправь видео в чат\n"
            "2. ответь на него командой:\n"
            "   /upload Название видео\n\n"
            "Prisma сгенерит описание и загрузит на YouTube )"
        )
        return

    title = " ".join(context.args)

    # Check if replying to a video
    reply = update.message.reply_to_message
    if not reply or not reply.video:
        await update.message.reply_text("○ ответь этой командой на видео")
        return

    video = reply.video

    # Check file size (Telegram limit ~20MB for bots)
    if video.file_size > 50 * 1024 * 1024:  # 50MB
        await update.message.reply_text("○ видео слишком большое (макс 50MB)")
        return

    await update.message.reply_text("● скачиваю видео...")

    try:
        # Download video
        file = await context.bot.get_file(video.file_id)
        file_path = f"/tmp/yt_upload_{video.file_id}.mp4"
        await file.download_to_drive(file_path)

        await update.message.reply_text("● генерю описание...")

        # Generate description with Gemini
        prisma = get_prisma_client()
        desc_prompt = f"""Сгенерируй описание для YouTube видео.

Название: {title}
Канал: Mycelium Media
Тематика: стартапы, микро-бизнесы, предпринимательство

Описание должно быть:
- 3-5 абзацев
- с эмодзи
- с призывом подписаться
- с хэштегами в конце

Формат:
[описание видео]

🔔 Подписывайтесь на канал!
💬 Пишите в комментариях...

#mycelium #стартап #бизнес"""

        description = await prisma.model.generate_content_async(desc_prompt)
        description_text = description.text.strip()

        # Generate tags
        tags = ["mycelium", "стартап", "бизнес", "предпринимательство"]

        await update.message.reply_text("● загружаю на YouTube...")

        # Upload to YouTube (as unlisted first for safety)
        result = yt.upload_video(
            file_path=file_path,
            title=title,
            description=description_text,
            tags=tags,
            privacy="unlisted"  # unlisted for safety, can change later
        )

        # Clean up temp file
        import os as os_module
        if os_module.path.exists(file_path):
            os_module.unlink(file_path)

        if result:
            await update.message.reply_text(
                f"✨ видео загружено!\n\n"
                f"▸ {result['url']}\n\n"
                f"статус: unlisted (можно поменять в YouTube Studio)\n\n"
                f"■ описание:\n{description_text[:500]}..."
            )
        else:
            await update.message.reply_text("○ ошибка загрузки")

    except Exception as e:
        logger.error(f"Upload error: {e}")
        await update.message.reply_text(f"○ ошибка: {str(e)[:100]}")


async def github_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /github - show GitHub repo stats"""
    gh = get_github_client()

    if not gh.is_available():
        await update.message.reply_text("○ GitHub не подключен. нужен GITHUB_TOKEN")
        return

    try:
        lines = [f"📊 GitHub: {gh.repo}", ""]

        # Recent commits
        commits = gh.get_today_commits()
        if commits:
            lines.append(f"▸ коммиты за сутки ({len(commits)}):")
            for c in commits[:5]:
                lines.append(f"  • {c['sha']} — {c['author']}: {c['message']}")
        else:
            lines.append("▸ коммитов за сутки нет")

        # Open PRs
        prs = gh.get_open_prs()
        if prs:
            lines.append(f"\n■ открытые PR ({len(prs)}):")
            for pr in prs[:5]:
                lines.append(f"  • #{pr['number']}: {pr['title']}")
        else:
            lines.append("\n■ открытых PR нет")

        # Merged PRs this week
        merged = gh.get_merged_prs(days=7)
        if merged:
            lines.append(f"\n● смержено за неделю ({len(merged)}):")
            for pr in merged[:5]:
                lines.append(f"  • #{pr['number']}: {pr['title']} ({pr['merged_at']})")

        # Issues
        issues = gh.get_recent_issues()
        lines.append(f"\n○ issues: {issues['open']} открыто, {issues['closed_today']} закрыто сегодня")

        await update.message.reply_text("\n".join(lines))

    except Exception as e:
        logger.error(f"GitHub command error: {e}")
        await update.message.reply_text(f"○ ошибка: {str(e)[:100]}")


async def mute_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /mute - toggle mute status (admin only)"""
    user = update.message.from_user
    username = user.username or ""
    chat_id = update.message.chat_id

    # Check if user is admin
    if username.lower() != ADMIN_USERNAME.lower():
        await update.message.reply_text("○ эта команда только для Артема")
        return

    # Check current status and toggle
    currently_muted = is_chat_muted(chat_id)

    if currently_muted:
        # Unmute
        set_chat_muted(chat_id, False)
        await update.message.reply_text(
            "🔔 prisma снова активна!\n\n"
            "● буду писать чекины и напоминания\n"
            "● отвечаю на сообщения как обычно"
        )
    else:
        # Mute
        set_chat_muted(chat_id, True)
        await update.message.reply_text(
            "🔕 prisma в тихом режиме\n\n"
            "○ не пишу чекины и напоминания\n"
            "○ отвечаю только когда позовёшь\n\n"
            "/mute — включить обратно"
        )


async def proactive_check(context: ContextTypes.DEFAULT_TYPE):
    """Proactive check - kick silent chats"""

    # Night mode: don't send messages between 23:00 and 9:00 (Spain time)
    if PYTZ_AVAILABLE:
        tz = pytz.timezone(TIMEZONE)
        current_hour = datetime.now(tz).hour
        if current_hour >= 23 or current_hour < 9:
            logger.info("Night mode: skipping proactive check")
            return

    logger.info("Running proactive check...")

    chats = get_all_active_chats()

    for chat_id in chats:
        try:
            # Skip muted chats
            if is_chat_muted(chat_id):
                continue

            silence = get_silence_duration(chat_id)

            kick_type = None

            if silence >= SILENCE_ALARM_HOURS:
                kick_type = "alarm"
            elif silence >= SILENCE_KICK_HOURS:
                kick_type = "gentle"
            elif random.random() < RANDOM_INSIGHT_CHANCE:
                kick_type = "insight"

            if kick_type:
                logger.info(f"Kicking chat {chat_id} with {kick_type}")

                prisma = get_prisma_client()
                message = await prisma.generate_kick_message(chat_id, kick_type)

                await context.bot.send_message(chat_id=chat_id, text=message)
                log_message(chat_id, 0, "Prisma", "assistant", message)
                update_last_kick_time(chat_id)

        except Exception as e:
            logger.error(f"Error kicking chat {chat_id}: {e}")


async def daily_checkin(context: ContextTypes.DEFAULT_TYPE):
    """Send daily check-in message to all active chats"""
    checkin_type = context.job.data.get("type", "afternoon")
    logger.info(f"Running daily {checkin_type} check-in...")

    chats = get_all_active_chats()

    if not chats:
        logger.info("No active chats for check-in")
        return

    # Get GitHub update
    github_update = ""
    github = get_github_client()
    if github.is_available():
        github_summary = github.get_summary()
        if github_summary:
            github_update = f"\n\nGITHUB_UPDATE:\n{github_summary}"

    # Get Google Docs update if available
    docs_update = ""
    if GOOGLE_DOCS_FOLDER_ID:
        docs_client = get_docs_client()
        if docs_client.is_available():
            docs_update = docs_client.get_recent_updates(GOOGLE_DOCS_FOLDER_ID)
            if docs_update:
                docs_update = f"\n\nDOCS_UPDATE:\n{docs_update}"

    # Get YouTube update
    youtube_update = ""
    yt = get_youtube_client()
    if yt.is_available():
        yt_summary = yt.get_summary()
        if yt_summary:
            youtube_update = f"\n\nYOUTUBE_UPDATE:\n{yt_summary}"

    for chat_id in chats:
        try:
            # Skip muted chats
            if is_chat_muted(chat_id):
                continue

            prisma = get_prisma_client()

            # Get checkin prompt
            prompt = CHECKIN_PROMPTS.get(checkin_type, CHECKIN_PROMPTS["afternoon"])

            # Add updates to prompt
            prompt += github_update + docs_update + youtube_update

            message = await prisma.generate_checkin_message(chat_id, checkin_type, prompt)

            await context.bot.send_message(chat_id=chat_id, text=message)
            log_message(chat_id, 0, "Prisma", "assistant", f"[{checkin_type.upper()}] {message}")

            logger.info(f"Sent {checkin_type} check-in to chat {chat_id}")

        except Exception as e:
            logger.error(f"Error sending check-in to {chat_id}: {e}")


def main():
    """Start Prisma bot"""
    if not PRISMA_BOT_TOKEN:
        raise ValueError("PRISMA_BOT_TOKEN is required")

    # Initialize database
    init_db()

    logger.info("Starting Prisma bot...")

    # Create application
    app = Application.builder().token(PRISMA_BOT_TOKEN).build()

    # Add handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("balance", balance_command))
    app.add_handler(CommandHandler("startidea", startidea_command))
    app.add_handler(CommandHandler("ideaprogress", ideaprogress_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("mute", mute_command))
    app.add_handler(CommandHandler("prompt", prompt_command))
    app.add_handler(CommandHandler("memory", memory_command))
    app.add_handler(CommandHandler("youtube", youtube_command))
    app.add_handler(CommandHandler("upload", upload_command))
    app.add_handler(CommandHandler("github", github_command))

    # Callback handlers for inline buttons
    app.add_handler(CallbackQueryHandler(handle_dialog_callback))

    # Handler for when bot is added to a group (welcome message)
    app.add_handler(ChatMemberHandler(
        handle_new_chat_member,
        ChatMemberHandler.MY_CHAT_MEMBER
    ))

    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        handle_message
    ))

    app.add_handler(MessageHandler(
        filters.PHOTO,
        handle_photo
    ))

    app.add_handler(MessageHandler(
        filters.VOICE,
        handle_voice
    ))

    # Add proactive job
    job_queue = app.job_queue
    job_queue.run_repeating(
        proactive_check,
        interval=PROACTIVE_CHECK_MINUTES * 60,
        first=60  # Start after 1 minute
    )

    # Schedule daily check-ins
    if PYTZ_AVAILABLE:
        tz = pytz.timezone(TIMEZONE)
        for checkin in DAILY_CHECKINS:
            checkin_time = time(
                hour=checkin["hour"],
                minute=checkin["minute"],
                tzinfo=tz
            )
            job_queue.run_daily(
                daily_checkin,
                time=checkin_time,
                data={"type": checkin["type"]}
            )
            logger.info(f"Scheduled {checkin['type']} check-in at {checkin['hour']:02d}:{checkin['minute']:02d} {TIMEZONE}")
    else:
        logger.warning("pytz not available, daily check-ins disabled")

    logger.info(f"{BOT_NAME} bot starting with proactive kicker and daily check-ins...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
