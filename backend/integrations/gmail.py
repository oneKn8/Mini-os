"""
Gmail OAuth integration and API client.
Based on patterns from GenerativeAIExamples/community/smart-health-agent/google_fit_utils.py
"""

import os
from datetime import datetime
from typing import Dict, List, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Gmail API scopes
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",  # Read emails
    "https://www.googleapis.com/auth/gmail.compose",  # Create drafts
]


class GmailClient:
    """Gmail API client with OAuth authentication."""

    def __init__(self, credentials: Optional[Credentials] = None):
        self.credentials = credentials
        self.service = None
        if credentials:
            self.service = build("gmail", "v1", credentials=credentials)

    @classmethod
    def authorize(cls, client_secrets_path: str) -> "GmailClient":
        """
        Start OAuth flow and return authenticated client.

        Args:
            client_secrets_path: Path to Gmail OAuth client secrets JSON

        Returns:
            Authenticated GmailClient
        """
        flow = InstalledAppFlow.from_client_secrets_file(client_secrets_path, SCOPES)
        credentials = flow.run_local_server(port=0)
        return cls(credentials)

    @classmethod
    def from_tokens(
        cls, access_token: str, refresh_token: str, token_uri: str, client_id: str, client_secret: str
    ) -> "GmailClient":
        """
        Create client from existing tokens.

        Args:
            access_token: OAuth access token
            refresh_token: OAuth refresh token
            token_uri: Token endpoint URL
            client_id: OAuth client ID
            client_secret: OAuth client secret

        Returns:
            Authenticated GmailClient
        """
        credentials = Credentials(
            token=access_token,
            refresh_token=refresh_token,
            token_uri=token_uri,
            client_id=client_id,
            client_secret=client_secret,
            scopes=SCOPES,
        )

        # Refresh if expired
        if credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())

        return cls(credentials)

    def fetch_messages(self, max_results: int = 50, query: str = "") -> List[Dict]:
        """
        Fetch recent emails.

        Args:
            max_results: Maximum number of emails to fetch
            query: Gmail search query (e.g., "is:unread")

        Returns:
            List of message dictionaries with normalized fields
        """
        if not self.service:
            raise ValueError("Gmail service not initialized")

        try:
            # List message IDs
            results = self.service.users().messages().list(userId="me", maxResults=max_results, q=query).execute()

            messages = results.get("messages", [])
            if not messages:
                return []

            # Fetch full message details
            detailed_messages = []
            for msg in messages:
                msg_data = self.service.users().messages().get(userId="me", id=msg["id"], format="full").execute()
                detailed_messages.append(self._normalize_message(msg_data))

            return detailed_messages

        except Exception as e:
            raise Exception(f"Error fetching Gmail messages: {e}")

    def _normalize_message(self, msg_data: Dict) -> Dict:
        """
        Normalize Gmail message to standard format.

        Args:
            msg_data: Raw Gmail API message data

        Returns:
            Normalized message dictionary
        """
        headers = {h["name"]: h["value"] for h in msg_data["payload"].get("headers", [])}

        # Extract body
        body_preview = msg_data.get("snippet", "")
        body_full = self._extract_body(msg_data["payload"])

        return {
            "source_id": msg_data["id"],
            "title": headers.get("Subject", "(No Subject)"),
            "body_preview": body_preview,
            "body_full": body_full,
            "sender": headers.get("From", ""),
            "recipients": [headers.get("To", "")],
            "received_datetime": datetime.fromtimestamp(int(msg_data["internalDate"]) / 1000),
            "raw_metadata": {
                "gmail": {
                    "message_id": msg_data["id"],
                    "thread_id": msg_data.get("threadId"),
                    "labels": msg_data.get("labelIds", []),
                }
            },
        }

    def _extract_body(self, payload: Dict) -> str:
        """Extract email body from message payload."""
        if "body" in payload and payload["body"].get("data"):
            import base64

            return base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="ignore")

        # Check parts for multipart messages
        if "parts" in payload:
            for part in payload["parts"]:
                if part["mimeType"] == "text/plain":
                    if part["body"].get("data"):
                        import base64

                        return base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="ignore")

        return ""

    def create_draft(self, to: str, subject: str, body: str) -> Dict:
        """
        Create a draft email.

        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body

        Returns:
            Draft metadata including draft_id
        """
        if not self.service:
            raise ValueError("Gmail service not initialized")

        import base64
        from email.mime.text import MIMEText

        message = MIMEText(body)
        message["to"] = to
        message["subject"] = subject

        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")

        draft = self.service.users().drafts().create(userId="me", body={"message": {"raw": raw_message}}).execute()

        return {"draft_id": draft["id"], "message_id": draft["message"]["id"]}
