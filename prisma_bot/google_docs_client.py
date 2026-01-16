"""Google Docs client for Prisma bot"""
import os
import json
import logging
from typing import Optional, List, Dict

logger = logging.getLogger(__name__)

# Try to import Google API
try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    GOOGLE_API_AVAILABLE = True
except ImportError:
    GOOGLE_API_AVAILABLE = False
    logger.warning("Google API not available")


class GoogleDocsClient:
    """Client for reading Google Docs"""

    def __init__(self):
        self.docs_service = None
        self.drive_service = None
        self._init_services()

    def _init_services(self):
        """Initialize Google services"""
        if not GOOGLE_API_AVAILABLE:
            logger.warning("Google API libraries not installed")
            return

        # Get credentials from environment
        creds_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "")

        if not creds_json:
            logger.warning("GOOGLE_SERVICE_ACCOUNT_JSON not set")
            return

        try:
            creds_data = json.loads(creds_json)
            credentials = service_account.Credentials.from_service_account_info(
                creds_data,
                scopes=[
                    'https://www.googleapis.com/auth/documents.readonly',
                    'https://www.googleapis.com/auth/drive.readonly'
                ]
            )

            self.docs_service = build('docs', 'v1', credentials=credentials)
            self.drive_service = build('drive', 'v3', credentials=credentials)
            logger.info("Google services initialized")

        except Exception as e:
            logger.error(f"Failed to init Google services: {e}")

    def is_available(self) -> bool:
        """Check if Google Docs is available"""
        return self.docs_service is not None

    def get_document(self, doc_id: str) -> Optional[str]:
        """Get document content by ID"""
        if not self.docs_service:
            return None

        try:
            doc = self.docs_service.documents().get(documentId=doc_id).execute()
            content = self._extract_text(doc)
            return content
        except Exception as e:
            logger.error(f"Error reading doc {doc_id}: {e}")
            return None

    def _extract_text(self, doc: dict) -> str:
        """Extract text from Google Doc"""
        text_parts = []

        content = doc.get('body', {}).get('content', [])

        for element in content:
            if 'paragraph' in element:
                paragraph = element['paragraph']
                for elem in paragraph.get('elements', []):
                    if 'textRun' in elem:
                        text_parts.append(elem['textRun'].get('content', ''))

        return ''.join(text_parts)

    def list_folder_docs(self, folder_id: str) -> List[Dict]:
        """List all documents in a folder"""
        if not self.drive_service:
            return []

        try:
            results = self.drive_service.files().list(
                q=f"'{folder_id}' in parents and mimeType='application/vnd.google-apps.document'",
                fields="files(id, name, modifiedTime)"
            ).execute()

            return results.get('files', [])
        except Exception as e:
            logger.error(f"Error listing folder {folder_id}: {e}")
            return []

    def get_recent_updates(self, folder_id: str, limit: int = 5) -> str:
        """Get summary of recent document updates"""
        docs = self.list_folder_docs(folder_id)

        if not docs:
            return "нет документов или нет доступа к папке"

        # Sort by modified time
        docs.sort(key=lambda x: x.get('modifiedTime', ''), reverse=True)

        summary_parts = []
        for doc in docs[:limit]:
            name = doc.get('name', 'без названия')
            modified = doc.get('modifiedTime', '')[:10]  # Just date
            summary_parts.append(f"▸ {name} (обновлен: {modified})")

        return "\n".join(summary_parts)


# Singleton instance
_docs_client = None

def get_docs_client() -> GoogleDocsClient:
    """Get singleton GoogleDocsClient"""
    global _docs_client
    if _docs_client is None:
        _docs_client = GoogleDocsClient()
    return _docs_client
