"""GitHub client for Prisma bot"""
import os
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict

logger = logging.getLogger(__name__)

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    logger.warning("requests not available")


class GitHubClient:
    """Client for reading GitHub repo updates"""

    def __init__(self):
        self.token = os.getenv("GITHUB_TOKEN", "")
        self.repo = os.getenv("GITHUB_REPO", "myceliummmm-sketch/mcards")
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }

    def is_available(self) -> bool:
        """Check if GitHub client is configured"""
        return bool(self.token and REQUESTS_AVAILABLE)

    def get_today_commits(self) -> List[Dict]:
        """Get commits from today"""
        if not self.is_available():
            return []

        try:
            since = (datetime.utcnow() - timedelta(days=1)).isoformat() + "Z"
            url = f"{self.base_url}/repos/{self.repo}/commits"
            params = {"since": since, "per_page": 20}

            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()

            commits = response.json()
            return [
                {
                    "sha": c["sha"][:7],
                    "message": c["commit"]["message"].split("\n")[0][:50],
                    "author": c["commit"]["author"]["name"]
                }
                for c in commits
            ]
        except Exception as e:
            logger.error(f"Error fetching commits: {e}")
            return []

    def get_open_prs(self) -> List[Dict]:
        """Get open pull requests"""
        if not self.is_available():
            return []

        try:
            url = f"{self.base_url}/repos/{self.repo}/pulls"
            params = {"state": "open", "per_page": 10}

            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()

            prs = response.json()
            return [
                {
                    "number": pr["number"],
                    "title": pr["title"][:40],
                    "author": pr["user"]["login"]
                }
                for pr in prs
            ]
        except Exception as e:
            logger.error(f"Error fetching PRs: {e}")
            return []

    def get_recent_issues(self) -> Dict:
        """Get issue stats"""
        if not self.is_available():
            return {"open": 0, "closed_today": 0}

        try:
            # Open issues
            url = f"{self.base_url}/repos/{self.repo}/issues"
            params = {"state": "open", "per_page": 100}

            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()
            open_count = len([i for i in response.json() if "pull_request" not in i])

            # Closed today
            since = (datetime.utcnow() - timedelta(days=1)).isoformat() + "Z"
            params = {"state": "closed", "since": since, "per_page": 100}

            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()
            closed_count = len([i for i in response.json() if "pull_request" not in i])

            return {"open": open_count, "closed_today": closed_count}
        except Exception as e:
            logger.error(f"Error fetching issues: {e}")
            return {"open": 0, "closed_today": 0}

    def get_summary(self) -> str:
        """Get formatted summary of repo activity"""
        if not self.is_available():
            return ""

        commits = self.get_today_commits()
        prs = self.get_open_prs()
        issues = self.get_recent_issues()

        lines = []

        if commits:
            lines.append(f"● {len(commits)} коммитов:")
            for c in commits[:5]:
                lines.append(f"  ○ {c['author']}: {c['message']}")

        if prs:
            lines.append(f"● {len(prs)} открытых PR:")
            for pr in prs[:3]:
                lines.append(f"  ○ #{pr['number']}: {pr['title']}")

        if issues["open"] > 0 or issues["closed_today"] > 0:
            lines.append(f"● issues: {issues['open']} открыто, {issues['closed_today']} закрыто сегодня")

        if not lines:
            return "○ в репо тихо, новых изменений нет"

        return "\n".join(lines)


# Singleton
_github_client = None


def get_github_client() -> GitHubClient:
    """Get singleton GitHubClient"""
    global _github_client
    if _github_client is None:
        _github_client = GitHubClient()
    return _github_client
