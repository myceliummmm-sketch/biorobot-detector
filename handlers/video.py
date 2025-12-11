import logging
from telegram import Update
from telegram.ext import ContextTypes

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
