"""Supabase client for Toxic bot - shared database with mcards"""
import logging
from typing import Optional, Dict, List
from config import SUPABASE_URL, SUPABASE_SERVICE_KEY

logger = logging.getLogger(__name__)

_client = None

def get_supabase():
    """Get Supabase client singleton"""
    global _client
    if _client is None:
        if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
            logger.warning("Supabase not configured, running without persistence")
            return None
        try:
            from supabase import create_client
            _client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
            logger.info(f"Connected to Supabase: {SUPABASE_URL}")
        except Exception as e:
            logger.error(f"Failed to connect to Supabase: {e}")
            return None
    return _client


def get_workspace_by_chat_id(chat_id: int) -> Optional[Dict]:
    """Get workspace from Supabase by Telegram group ID"""
    client = get_supabase()
    if not client:
        return None
    try:
        result = client.table("workspaces")\
            .select("*")\
            .eq("telegram_group_id", chat_id)\
            .execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"Error getting workspace: {e}")
        return None


def get_workspace_cards(workspace_id: str) -> List[Dict]:
    """Get all cards for a workspace"""
    client = get_supabase()
    if not client:
        return []
    try:
        result = client.table("cards")\
            .select("*")\
            .eq("workspace_id", workspace_id)\
            .order("slot")\
            .execute()
        return result.data or []
    except Exception as e:
        logger.error(f"Error getting cards: {e}")
        return []


def get_ai_history(workspace_id: str, agent: str = "toxic", limit: int = 20) -> List[Dict]:
    """Get recent AI conversation history for this agent"""
    client = get_supabase()
    if not client:
        return []
    try:
        result = client.table("ai_conversations")\
            .select("*")\
            .eq("workspace_id", workspace_id)\
            .eq("agent", agent)\
            .order("created_at", desc=True)\
            .limit(limit)\
            .execute()
        return list(reversed(result.data)) if result.data else []
    except Exception as e:
        logger.error(f"Error getting AI history: {e}")
        return []


def save_ai_message(workspace_id: str, user_id: int, agent: str, role: str, content: str):
    """Save message to AI conversation history"""
    client = get_supabase()
    if not client:
        return
    try:
        # Get or create profile for telegram user
        profile_id = get_or_create_profile(user_id)

        client.table("ai_conversations").insert({
            "workspace_id": workspace_id,
            "user_id": profile_id,
            "agent": agent,
            "role": role,
            "content": content[:4000]  # Truncate if too long
        }).execute()
    except Exception as e:
        logger.error(f"Error saving AI message: {e}")


def get_or_create_profile(telegram_id: int, username: str = None, first_name: str = None) -> Optional[str]:
    """Get existing profile or create new one for Telegram user"""
    client = get_supabase()
    if not client:
        return None
    try:
        # Try to find existing profile
        result = client.table("profiles")\
            .select("id")\
            .eq("telegram_id", telegram_id)\
            .execute()

        if result.data:
            return result.data[0]["id"]

        # Create new profile
        new_profile = client.table("profiles").insert({
            "telegram_id": telegram_id,
            "telegram_username": username,
            "username": first_name or f"user_{telegram_id}"
        }).execute()

        return new_profile.data[0]["id"] if new_profile.data else None
    except Exception as e:
        logger.error(f"Error with profile: {e}")
        return None


def build_workspace_context(chat_id: int) -> str:
    """Build context string for AI from workspace data"""
    workspace = get_workspace_by_chat_id(chat_id)
    if not workspace:
        return ""

    cards = get_workspace_cards(workspace["id"])

    # Format filled cards
    cards_summary = []
    for card in cards:
        if card.get("fill_rate", 0) > 0:
            data = card.get("data", {})
            if data:
                cards_summary.append(f"- {card['type']}: {str(data)[:200]}")

    context = f"""
=== КОНТЕКСТ ПРОЕКТА ===
Название: {workspace['name']}
Режим: {workspace.get('mode', 'chill')}
PMF Score: {workspace.get('pmf_score', 0)}%
Battery: {workspace.get('battery', 100)}%

Заполненные карточки:
{chr(10).join(cards_summary) if cards_summary else 'Пока пусто - проект только начинается'}
"""
    return context
