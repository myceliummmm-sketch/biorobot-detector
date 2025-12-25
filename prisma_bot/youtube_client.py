import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# Check if google API client is available
try:
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    YOUTUBE_AVAILABLE = True
except ImportError:
    YOUTUBE_AVAILABLE = False
    logger.warning("google-api-python-client not installed, YouTube integration disabled")


class YouTubeClient:
    def __init__(self):
        self.client_id = os.getenv("YOUTUBE_CLIENT_ID", "")
        self.client_secret = os.getenv("YOUTUBE_CLIENT_SECRET", "")
        self.refresh_token = os.getenv("YOUTUBE_REFRESH_TOKEN", "")

        self.youtube = None
        self.youtube_analytics = None
        self.channel_id = None

        if not YOUTUBE_AVAILABLE:
            logger.warning("YouTube client disabled - missing dependencies")
            return

        if not all([self.client_id, self.client_secret, self.refresh_token]):
            logger.warning("YouTube credentials not configured")
            return

        try:
            self._authenticate()
            logger.info("YouTube client initialized")
        except Exception as e:
            logger.error(f"YouTube auth failed: {e}")

    def _authenticate(self):
        """Authenticate with YouTube API using refresh token"""
        creds = Credentials(
            token=None,
            refresh_token=self.refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=self.client_id,
            client_secret=self.client_secret,
            scopes=[
                "https://www.googleapis.com/auth/youtube.readonly",
                "https://www.googleapis.com/auth/yt-analytics.readonly"
            ]
        )

        # Refresh the token
        creds.refresh(Request())

        # Build API clients
        self.youtube = build("youtube", "v3", credentials=creds)
        self.youtube_analytics = build("youtubeAnalytics", "v2", credentials=creds)

        # Get channel ID
        response = self.youtube.channels().list(
            part="id",
            mine=True
        ).execute()

        if response.get("items"):
            self.channel_id = response["items"][0]["id"]
            logger.info(f"Connected to channel: {self.channel_id}")

    def is_available(self) -> bool:
        """Check if YouTube client is ready"""
        return self.youtube is not None and self.channel_id is not None

    def get_channel_stats(self) -> Optional[Dict]:
        """Get basic channel statistics"""
        if not self.is_available():
            return None

        try:
            response = self.youtube.channels().list(
                part="statistics,snippet",
                id=self.channel_id
            ).execute()

            if not response.get("items"):
                return None

            channel = response["items"][0]
            stats = channel["statistics"]

            return {
                "title": channel["snippet"]["title"],
                "subscribers": int(stats.get("subscriberCount", 0)),
                "total_views": int(stats.get("viewCount", 0)),
                "video_count": int(stats.get("videoCount", 0))
            }
        except Exception as e:
            logger.error(f"Error getting channel stats: {e}")
            return None

    def get_recent_videos(self, limit: int = 5) -> List[Dict]:
        """Get recent uploaded videos with stats"""
        if not self.is_available():
            return []

        try:
            # Get uploads playlist
            response = self.youtube.channels().list(
                part="contentDetails",
                id=self.channel_id
            ).execute()

            if not response.get("items"):
                return []

            uploads_playlist = response["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

            # Get recent videos from playlist
            response = self.youtube.playlistItems().list(
                part="snippet",
                playlistId=uploads_playlist,
                maxResults=limit
            ).execute()

            video_ids = [item["snippet"]["resourceId"]["videoId"] for item in response.get("items", [])]

            if not video_ids:
                return []

            # Get video statistics
            response = self.youtube.videos().list(
                part="statistics,snippet",
                id=",".join(video_ids)
            ).execute()

            videos = []
            for item in response.get("items", []):
                stats = item["statistics"]
                videos.append({
                    "title": item["snippet"]["title"][:50],
                    "published": item["snippet"]["publishedAt"][:10],
                    "views": int(stats.get("viewCount", 0)),
                    "likes": int(stats.get("likeCount", 0)),
                    "comments": int(stats.get("commentCount", 0))
                })

            return videos
        except Exception as e:
            logger.error(f"Error getting recent videos: {e}")
            return []

    def get_analytics_last_days(self, days: int = 7) -> Optional[Dict]:
        """Get analytics for last N days (requires YouTube Analytics API)"""
        if not self.is_available() or not self.youtube_analytics:
            return None

        try:
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

            response = self.youtube_analytics.reports().query(
                ids=f"channel=={self.channel_id}",
                startDate=start_date,
                endDate=end_date,
                metrics="views,estimatedMinutesWatched,averageViewDuration,subscribersGained,subscribersLost",
                dimensions="day",
                sort="day"
            ).execute()

            rows = response.get("rows", [])

            if not rows:
                return None

            # Aggregate data
            total_views = sum(row[1] for row in rows)
            total_watch_time = sum(row[2] for row in rows)
            subs_gained = sum(row[4] for row in rows)
            subs_lost = sum(row[5] for row in rows)

            return {
                "period_days": days,
                "views": int(total_views),
                "watch_hours": round(total_watch_time / 60, 1),
                "subs_gained": int(subs_gained),
                "subs_lost": int(subs_lost),
                "subs_net": int(subs_gained - subs_lost)
            }
        except Exception as e:
            logger.error(f"Error getting analytics: {e}")
            return None

    def get_summary(self) -> str:
        """Get formatted summary for bot messages"""
        if not self.is_available():
            return ""

        lines = []

        # Channel stats
        stats = self.get_channel_stats()
        if stats:
            lines.append(f"📺 {stats['title']}")
            lines.append(f"   подписчиков: {stats['subscribers']:,}")

        # Weekly analytics
        analytics = self.get_analytics_last_days(7)
        if analytics:
            lines.append(f"   за неделю: {analytics['views']:,} просмотров")
            if analytics['subs_net'] > 0:
                lines.append(f"   новых подписчиков: +{analytics['subs_net']}")
            elif analytics['subs_net'] < 0:
                lines.append(f"   подписчиков: {analytics['subs_net']}")

        # Recent video
        videos = self.get_recent_videos(1)
        if videos:
            v = videos[0]
            lines.append(f"   последнее видео: {v['views']:,} просмотров")

        return "\n".join(lines) if lines else ""


# Singleton
_client = None


def get_youtube_client() -> YouTubeClient:
    global _client
    if _client is None:
        _client = YouTubeClient()
    return _client
