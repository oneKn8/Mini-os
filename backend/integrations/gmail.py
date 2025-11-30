"""
Gmail OAuth integration and API client.
Based on patterns from GenerativeAIExamples/community/smart-health-agent/google_fit_utils.py
"""

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


def _parse_ics(ics_text: str) -> Dict:
    """
    Minimal ICS parser to pull out key invite fields.
    - Handles unfolded lines (basic folding).
    - Extracts SUMMARY, LOCATION, STATUS, DTSTART, DTEND, DESCRIPTION, URL, ATTENDEE.
    - Returns raw strings; date parsing is done best-effort (ISO if possible).
    """
    if not ics_text:
        return {}

    # Unfold lines (lines starting with space are continuations)
    lines: List[str] = []
    for raw in ics_text.splitlines():
        if raw.startswith(" ") and lines:
            lines[-1] += raw.strip()
        else:
            lines.append(raw.strip())

    def parse_datetime(value: str) -> Optional[str]:
        # Basic ISO-like conversion; many invites use YYYYMMDDTHHMMSSZ
        try:
            if value.endswith("Z"):
                return datetime.strptime(value, "%Y%m%dT%H%M%SZ").isoformat() + "Z"
            # Fallback to naive datetime
            return datetime.strptime(value, "%Y%m%dT%H%M%S").isoformat()
        except Exception:
            return value  # return raw if unknown format

    result: Dict[str, object] = {
        "attendees": [],
    }

    for line in lines:
        if ":" not in line:
            continue
        name_part, value = line.split(":", 1)
        name = name_part.split(";")[0].upper().strip()
        val = value.strip()

        if name == "SUMMARY":
            result["summary"] = val
        elif name == "LOCATION":
            result["location"] = val
        elif name == "STATUS":
            result["status"] = val
        elif name == "DESCRIPTION":
            result["description"] = val
        elif name == "URL":
            result["url"] = val
        elif name == "DTSTART":
            result["start"] = parse_datetime(val)
        elif name == "DTEND":
            result["end"] = parse_datetime(val)
        elif name == "ATTENDEE":
            # Extract email from mailto if present
            email = val
            if val.lower().startswith("mailto:"):
                email = val[7:]
            result["attendees"].append(email)

    return result


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

    def fetch_messages(
        self,
        max_results: int = 50,
        query: str = "",
        page_token: Optional[str] = None,
    ) -> Dict[str, object]:
        """
        Fetch recent emails.

        Args:
            max_results: Maximum number of emails to fetch
            query: Gmail search query (e.g., "is:unread")
            page_token: Optional page token for pagination

        Returns:
            Dict with messages list and next_page_token (if any)
        """
        if not self.service:
            raise ValueError("Gmail service not initialized")

        try:
            # List message IDs
            list_kwargs: Dict[str, object] = {"userId": "me", "maxResults": max_results}
            if query:
                list_kwargs["q"] = query
            if page_token:
                list_kwargs["pageToken"] = page_token

            results = self.service.users().messages().list(**list_kwargs).execute()

            messages = results.get("messages", [])
            if not messages:
                return {"messages": [], "next_page_token": None}

            # Fetch full message details
            detailed_messages = []
            for msg in messages:
                msg_data = self.service.users().messages().get(userId="me", id=msg["id"], format="full").execute()
                detailed_messages.append(self._normalize_message(msg_data))

            return {
                "messages": detailed_messages,
                "next_page_token": results.get("nextPageToken"),
            }

        except Exception as e:
            raise Exception(f"Error fetching Gmail messages: {e}")

    def fetch_message_by_id(self, message_id: str) -> Dict:
        """Fetch a single message by ID and normalize it."""
        if not self.service:
            raise ValueError("Gmail service not initialized")
        msg_data = self.service.users().messages().get(userId="me", id=message_id, format="full").execute()
        return self._normalize_message(msg_data)

    def _normalize_message(self, msg_data: Dict) -> Dict:
        """
        Normalize Gmail message to standard format.

        Args:
            msg_data: Raw Gmail API message data

        Returns:
            Normalized message dictionary
        """
        headers = {h["name"]: h["value"] for h in msg_data["payload"].get("headers", [])}

        # Extract body variants and calendar data
        body_preview = msg_data.get("snippet", "")
        bodies = self._extract_bodies(msg_data["payload"])
        body_full = bodies.get("html") or bodies.get("text") or ""
        calendar_raw = bodies.get("calendar") or ""
        calendar_parsed = _parse_ics(calendar_raw) if calendar_raw else {}

        normalized = {
            "source_id": msg_data["id"],
            "thread_id": msg_data.get("threadId"),
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
                    "calendar_body": calendar_raw or None,
                    "calendar_parsed": calendar_parsed or None,
                }
            },
        }

        return normalized

    def _extract_bodies(self, payload: Dict) -> Dict[str, Optional[str]]:
        """Extract text/html, text/plain, and text/calendar bodies from a message payload."""
        import base64

        html_parts: List[str] = []
        text_parts: List[str] = []
        calendar_parts: List[str] = []

        def decode_body(part: Dict) -> str:
            data = part.get("body", {}).get("data")
            if not data:
                return ""
            try:
                return base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
            except Exception:
                return ""

        def walk(part: Dict):
            mime = (part.get("mimeType") or "").lower()

            if mime.startswith("text/html"):
                content = decode_body(part)
                if content:
                    html_parts.append(content)
            elif mime.startswith("text/plain"):
                content = decode_body(part)
                if content:
                    text_parts.append(content)
            elif mime.startswith("text/calendar"):
                content = decode_body(part)
                if content:
                    calendar_parts.append(content)

            # Recurse into child parts
            for child in part.get("parts", []) or []:
                walk(child)

        walk(payload)

        bodies: Dict[str, Optional[str]] = {
            "html": html_parts[0] if html_parts else None,
            "text": text_parts[0] if text_parts else None,
            "calendar": calendar_parts[0] if calendar_parts else None,
        }

        return bodies

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
