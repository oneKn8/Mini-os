"""
Outlook/Microsoft Graph OAuth integration and API client.
"""

from datetime import datetime
from typing import Dict, List, Optional

import msal
import requests


class OutlookClient:
    """Outlook API client using Microsoft Graph."""

    def __init__(self, access_token: str):
        self.access_token = access_token
        self.headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
        self.graph_url = "https://graph.microsoft.com/v1.0"

    @classmethod
    def authorize(cls, client_id: str, client_secret: str, tenant_id: str = "common") -> "OutlookClient":
        """Authorize using client credentials flow."""
        authority = f"https://login.microsoftonline.com/{tenant_id}"
        scopes = ["https://graph.microsoft.com/.default"]

        app = msal.ConfidentialClientApplication(client_id, authority=authority, client_credential=client_secret)

        result = app.acquire_token_for_client(scopes=scopes)

        if "access_token" in result:
            return cls(result["access_token"])
        else:
            raise Exception(f"Failed to acquire token: {result.get('error_description')}")

    @classmethod
    def from_refresh_token(
        cls, client_id: str, client_secret: str, refresh_token: str, tenant_id: str = "common"
    ) -> "OutlookClient":
        """Get new access token from refresh token."""
        authority = f"https://login.microsoftonline.com/{tenant_id}"
        scopes = ["https://graph.microsoft.com/Mail.Read", "https://graph.microsoft.com/Mail.ReadWrite"]

        app = msal.ConfidentialClientApplication(client_id, authority=authority, client_credential=client_secret)

        result = app.acquire_token_by_refresh_token(refresh_token, scopes=scopes)

        if "access_token" in result:
            return cls(result["access_token"])
        else:
            raise Exception(f"Failed to refresh token: {result.get('error_description')}")

    def fetch_messages(self, max_results: int = 50, filter_query: str = "") -> List[Dict]:
        """Fetch recent emails from Outlook."""
        url = f"{self.graph_url}/me/messages"
        params = {"$top": max_results, "$orderby": "receivedDateTime DESC"}

        if filter_query:
            params["$filter"] = filter_query

        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()

        messages = response.json().get("value", [])
        return [self._normalize_message(msg) for msg in messages]

    def _normalize_message(self, msg_data: Dict) -> Dict:
        """Normalize Outlook message to standard format."""
        return {
            "source_id": msg_data["id"],
            "title": msg_data.get("subject", "(No Subject)"),
            "body_preview": msg_data.get("bodyPreview", ""),
            "body_full": msg_data.get("body", {}).get("content", ""),
            "sender": msg_data.get("from", {}).get("emailAddress", {}).get("address", ""),
            "recipients": [r.get("emailAddress", {}).get("address", "") for r in msg_data.get("toRecipients", [])],
            "received_datetime": datetime.fromisoformat(msg_data["receivedDateTime"].replace("Z", "+00:00")),
            "raw_metadata": {
                "outlook": {
                    "conversation_id": msg_data.get("conversationId"),
                    "is_read": msg_data.get("isRead", False),
                    "importance": msg_data.get("importance", "normal"),
                }
            },
        }

    def create_draft(self, to: str, subject: str, body: str) -> Dict:
        """Create a draft email in Outlook."""
        url = f"{self.graph_url}/me/messages"

        draft_data = {
            "subject": subject,
            "body": {"contentType": "Text", "content": body},
            "toRecipients": [{"emailAddress": {"address": to}}],
        }

        response = requests.post(url, headers=self.headers, json=draft_data)
        response.raise_for_status()

        result = response.json()
        return {"draft_id": result["id"], "conversation_id": result.get("conversationId")}
