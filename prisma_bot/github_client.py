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

    def get_merged_prs(self, days: int = 7) -> List[Dict]:
        """Get recently merged pull requests"""
        if not self.is_available():
            return []

        try:
            since = (datetime.utcnow() - timedelta(days=days)).isoformat() + "Z"
            url = f"{self.base_url}/repos/{self.repo}/pulls"
            params = {"state": "closed", "sort": "updated", "direction": "desc", "per_page": 20}

            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()

            merged = []
            for pr in response.json():
                if pr.get("merged_at"):
                    merged_at = datetime.fromisoformat(pr["merged_at"].replace("Z", "+00:00"))
                    if merged_at > datetime.now(merged_at.tzinfo) - timedelta(days=days):
                        merged.append({
                            "number": pr["number"],
                            "title": pr["title"],
                            "author": pr["user"]["login"],
                            "merged_at": pr["merged_at"][:10],
                            "merged_by": pr.get("merged_by", {}).get("login", "unknown"),
                            "commits": pr.get("commits", 0),
                            "additions": pr.get("additions", 0),
                            "deletions": pr.get("deletions", 0)
                        })
            return merged
        except Exception as e:
            logger.error(f"Error fetching merged PRs: {e}")
            return []

    def get_pr_details(self, pr_number: int) -> Optional[Dict]:
        """Get detailed info about a specific PR"""
        if not self.is_available():
            return None

        try:
            url = f"{self.base_url}/repos/{self.repo}/pulls/{pr_number}"
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            pr = response.json()

            # Get commits for this PR
            commits_url = f"{self.base_url}/repos/{self.repo}/pulls/{pr_number}/commits"
            commits_response = requests.get(commits_url, headers=self.headers, timeout=10)
            commits = commits_response.json() if commits_response.ok else []

            return {
                "number": pr["number"],
                "title": pr["title"],
                "author": pr["user"]["login"],
                "state": pr["state"],
                "merged": pr.get("merged", False),
                "merged_at": pr.get("merged_at"),
                "created_at": pr["created_at"][:10],
                "commits_count": pr.get("commits", 0),
                "additions": pr.get("additions", 0),
                "deletions": pr.get("deletions", 0),
                "commits": [
                    {
                        "sha": c["sha"][:7],
                        "message": c["commit"]["message"].split("\n")[0][:60],
                        "author": c["commit"]["author"]["name"]
                    }
                    for c in commits[:10]
                ]
            }
        except Exception as e:
            logger.error(f"Error fetching PR #{pr_number}: {e}")
            return None

    def get_branch_commits(self, branch: str = "main", count: int = 10) -> List[Dict]:
        """Get recent commits from a specific branch"""
        if not self.is_available():
            return []

        try:
            url = f"{self.base_url}/repos/{self.repo}/commits"
            params = {"sha": branch, "per_page": count}

            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()

            return [
                {
                    "sha": c["sha"][:7],
                    "message": c["commit"]["message"].split("\n")[0],
                    "author": c["commit"]["author"]["name"],
                    "date": c["commit"]["author"]["date"][:10]
                }
                for c in response.json()
            ]
        except Exception as e:
            logger.error(f"Error fetching branch commits: {e}")
            return []

    def get_full_summary(self) -> str:
        """Get detailed summary for smart context"""
        if not self.is_available():
            return "GitHub не подключен"

        lines = [f"📊 GitHub: {self.repo}"]

        # Recent commits
        commits = self.get_today_commits()
        if commits:
            lines.append(f"\n▸ Коммиты за сутки ({len(commits)}):")
            for c in commits[:5]:
                lines.append(f"  • {c['sha']} — {c['author']}: {c['message']}")

        # Open PRs
        prs = self.get_open_prs()
        if prs:
            lines.append(f"\n▸ Открытые PR ({len(prs)}):")
            for pr in prs[:5]:
                lines.append(f"  • #{pr['number']}: {pr['title']} (@{pr['author']})")

        # Merged PRs this week
        merged = self.get_merged_prs(days=7)
        if merged:
            lines.append(f"\n▸ Смержено за неделю ({len(merged)}):")
            for pr in merged[:5]:
                lines.append(f"  • #{pr['number']}: {pr['title']} ({pr['merged_at']})")

        # Issues
        issues = self.get_recent_issues()
        lines.append(f"\n▸ Issues: {issues['open']} открыто, {issues['closed_today']} закрыто сегодня")

        return "\n".join(lines)

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
