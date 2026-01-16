"""
Supabase Bridge Client for Telegram Bot

Async client using aiohttp to communicate with Supabase Edge Function:
{SUPABASE_URL}/functions/v1/telegram-bot-bridge

Actions supported:
- sync_user_status: Upsert user data (Telegram ID, username, quiz results)
- get_project_status: Returns passport status, vision_progress, project phase
- get_syndicate_pulse: Social proof feed of recent activities
"""

import logging
import aiohttp
from typing import Optional, Dict, Any

from config import SUPABASE_BRIDGE_URL, SUPABASE_ANON_KEY

logger = logging.getLogger(__name__)


class SupabaseClient:
    """Async client for Supabase Edge Function bridge"""

    def __init__(self):
        self.bridge_url = SUPABASE_BRIDGE_URL
        self.headers = {
            "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
            "Content-Type": "application/json"
        }
        self._enabled = bool(SUPABASE_BRIDGE_URL and SUPABASE_ANON_KEY)

        if not self._enabled:
            logger.warning("Supabase not configured - running in local-only mode")

    @property
    def is_enabled(self) -> bool:
        return self._enabled

    async def _request(self, action: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Make async request to Supabase bridge"""
        if not self._enabled:
            logger.debug(f"Supabase disabled, skipping action: {action}")
            return None

        payload = {"action": action, **data}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.bridge_url,
                    json=payload,
                    headers=self.headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info(f"Supabase {action} success: {result}")
                        return result
                    else:
                        error_text = await response.text()
                        logger.error(f"Supabase {action} failed ({response.status}): {error_text}")
                        return None
        except aiohttp.ClientError as e:
            logger.error(f"Supabase connection error for {action}: {e}")
            return None
        except Exception as e:
            logger.error(f"Supabase unexpected error for {action}: {e}")
            return None

    async def sync_user_status(
        self,
        telegram_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        quiz_blocker: Optional[str] = None,
        assigned_character: Optional[str] = None,
        quiz_score: Optional[int] = None,
        onboarding_step: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Sync user data to Supabase (upsert)

        Args:
            telegram_id: Telegram user ID
            username: Telegram username
            first_name: User's first name
            quiz_blocker: Detected blocker (e.g., "Страх выбора")
            assigned_character: Character key (e.g., "prisma", "ever")
            quiz_score: Quiz score (0-100)
            onboarding_step: Current step (e.g., "quiz_complete", "vision_started")
        """
        data = {
            "telegram_id": telegram_id,
            "username": username,
            "first_name": first_name,
        }

        # Add optional quiz results
        if quiz_blocker:
            data["quiz_blocker"] = quiz_blocker
        if assigned_character:
            data["assigned_character"] = assigned_character
        if quiz_score is not None:
            data["quiz_score"] = quiz_score
        if onboarding_step:
            data["onboarding_step"] = onboarding_step

        return await self._request("sync_user_status", data)

    async def get_project_status(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        """
        Get user's project status from Supabase

        Returns:
            {
                "has_passport": bool,
                "vision_progress": int (0-100),
                "build_progress": int (0-100),
                "current_phase": str ("idea" | "build" | "ship"),
                "assigned_character": str,
                "quiz_blocker": str
            }
        """
        return await self._request("get_project_status", {"telegram_id": telegram_id})

    async def get_syndicate_pulse(self, limit: int = 5) -> Optional[Dict[str, Any]]:
        """
        Get recent syndicate activity for social proof

        Returns:
            {
                "activities": [
                    {"user": "...", "action": "completed_vision", "time_ago": "2h"},
                    ...
                ],
                "total_users": int,
                "active_today": int
            }
        """
        return await self._request("get_syndicate_pulse", {"limit": limit})


# Singleton instance
_client: Optional[SupabaseClient] = None


def get_supabase_client() -> SupabaseClient:
    """Get or create Supabase client singleton"""
    global _client
    if _client is None:
        _client = SupabaseClient()
    return _client
