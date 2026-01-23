"""
AI Service for Toxic bot using Google Gemini
"""

import logging
import google.generativeai as genai
from config import GEMINI_API_KEY

logger = logging.getLogger(__name__)

# Configure Gemini
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# Initialize model
model = None
if GEMINI_API_KEY:
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        generation_config={
            "temperature": 0.8,
            "top_p": 0.95,
            "max_output_tokens": 1024,
        }
    )

async def generate_response(user_message: str, system_prompt: str) -> str:
    """
    Generate response using Gemini

    Args:
        user_message: User's message
        system_prompt: System prompt with character definition

    Returns:
        Generated response text
    """
    if not model:
        return "☢️ AI не подключен. нужен GEMINI_API_KEY"

    try:
        # Build full prompt
        full_prompt = f"""{system_prompt}

---

{user_message}"""

        # Generate response
        response = await model.generate_content_async(full_prompt)

        return response.text.strip()

    except Exception as e:
        logger.error(f"Gemini error: {e}")
        return f"☢️ ошибка: {str(e)[:100]}"
