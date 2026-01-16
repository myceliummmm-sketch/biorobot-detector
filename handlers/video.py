import logging
from telegram import Update
from telegram.ext import ContextTypes

from content.videos import VIDEOS

logger = logging.getLogger(__name__)


async def video_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle video uploads - returns file_id for adding to videos.py"""
    video = update.message.video
    file_id = video.file_id

    response = f"""📹 **Video received!**

**file_id:**
```
{file_id}
```

Copy this file_id and add it to `content/videos.py`"""

    await update.message.reply_text(response, parse_mode="Markdown")
    logger.info(f"Video file_id captured: {file_id[:20]}...")


async def download_all_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send all videos for download with proper filenames"""

    # Только нужные для сайта (результат квиза)
    videos_to_send = {
        "phoenix_success.mp4": VIDEOS.get("phoenix_success"),
        "ever_blocker.mp4": VIDEOS.get("ever_blocker"),
        "prisma_blocker.mp4": VIDEOS.get("prisma_blocker"),
        "zen_blocker.mp4": VIDEOS.get("zen_blocker"),
        "toxic_blocker.mp4": VIDEOS.get("toxic_blocker"),
        "tech_priest_blocker.mp4": VIDEOS.get("tech_priest_blocker"),
    }

    await update.message.reply_text("📥 Отправляю видео для скачивания...")

    sent = 0
    for filename, file_id in videos_to_send.items():
        if file_id:
            try:
                await update.message.reply_document(
                    document=file_id,
                    filename=filename,
                    caption=f"📁 {filename}"
                )
                sent += 1
            except Exception as e:
                logger.error(f"Failed to send {filename}: {e}")
                await update.message.reply_text(f"❌ Ошибка: {filename}")

    await update.message.reply_text(f"✅ Отправлено {sent}/6 видео. Скачай и загрузи в Lovable!")
