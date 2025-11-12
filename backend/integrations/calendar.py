"""
Google Calendar OAuth integration and API client.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/calendar"]


class CalendarClient:
    """Google Calendar API client."""

    def __init__(self, credentials: Optional[Credentials] = None):
        self.credentials = credentials
        self.service = None
        if credentials:
            self.service = build("calendar", "v3", credentials=credentials)

    @classmethod
    def authorize(cls, client_secrets_path: str) -> "CalendarClient":
        """Start OAuth flow."""
        flow = InstalledAppFlow.from_client_secrets_file(client_secrets_path, SCOPES)
        credentials = flow.run_local_server(port=0)
        return cls(credentials)

    @classmethod
    def from_tokens(
        cls, access_token: str, refresh_token: str, token_uri: str, client_id: str, client_secret: str
    ) -> "CalendarClient":
        """Create client from tokens."""
        credentials = Credentials(
            token=access_token,
            refresh_token=refresh_token,
            token_uri=token_uri,
            client_id=client_id,
            client_secret=client_secret,
            scopes=SCOPES,
        )

        if credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())

        return cls(credentials)

    def fetch_events(self, days_ahead: int = 14) -> List[Dict]:
        """Fetch upcoming calendar events."""
        if not self.service:
            raise ValueError("Calendar service not initialized")

        now = datetime.utcnow()
        time_min = now.isoformat() + "Z"
        time_max = (now + timedelta(days=days_ahead)).isoformat() + "Z"

        events_result = (
            self.service.events()
            .list(
                calendarId="primary",
                timeMin=time_min,
                timeMax=time_max,
                maxResults=100,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )

        events = events_result.get("items", [])
        return [self._normalize_event(event) for event in events]

    def _normalize_event(self, event_data: Dict) -> Dict:
        """Normalize Calendar event to standard format."""
        start = event_data.get("start", {})
        end = event_data.get("end", {})

        start_dt = start.get("dateTime") or start.get("date")
        end_dt = end.get("dateTime") or end.get("date")

        return {
            "source_id": event_data["id"],
            "title": event_data.get("summary", "(No Title)"),
            "body_preview": event_data.get("description", "")[:500],
            "body_full": event_data.get("description", ""),
            "sender": event_data.get("organizer", {}).get("email", ""),
            "recipients": [a.get("email", "") for a in event_data.get("attendees", [])],
            "start_datetime": datetime.fromisoformat(start_dt.replace("Z", "+00:00")),
            "end_datetime": datetime.fromisoformat(end_dt.replace("Z", "+00:00")),
            "received_datetime": datetime.fromisoformat(event_data["created"].replace("Z", "+00:00")),
            "raw_metadata": {
                "google_calendar": {
                    "event_id": event_data["id"],
                    "status": event_data.get("status"),
                    "location": event_data.get("location"),
                    "html_link": event_data.get("htmlLink"),
                }
            },
        }

    def create_event(
        self, title: str, start: datetime, end: datetime, description: str = "", location: str = ""
    ) -> Dict:
        """Create a calendar event."""
        if not self.service:
            raise ValueError("Calendar service not initialized")

        event = {
            "summary": title,
            "description": description,
            "start": {"dateTime": start.isoformat(), "timeZone": "UTC"},
            "end": {"dateTime": end.isoformat(), "timeZone": "UTC"},
        }

        if location:
            event["location"] = location

        created_event = self.service.events().insert(calendarId="primary", body=event).execute()

        return {"event_id": created_event["id"], "html_link": created_event.get("htmlLink")}

    def update_event(self, event_id: str, **updates) -> Dict:
        """Update an existing event."""
        if not self.service:
            raise ValueError("Calendar service not initialized")

        event = self.service.events().get(calendarId="primary", eventId=event_id).execute()

        for key, value in updates.items():
            event[key] = value

        updated_event = self.service.events().update(calendarId="primary", eventId=event_id, body=event).execute()

        return {"event_id": updated_event["id"], "updated": updated_event["updated"]}

    def delete_event(self, event_id: str) -> bool:
        """Delete a calendar event."""
        if not self.service:
            raise ValueError("Calendar service not initialized")

        self.service.events().delete(calendarId="primary", eventId=event_id).execute()
        return True
