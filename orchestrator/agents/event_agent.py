"""
Event Agent - Extracts and proposes calendar events.
"""

import json
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List

import requests

from orchestrator.agents.base import AgentContext, AgentResult, BaseAgent


class EventAgent(BaseAgent):
    """Agent for calendar event extraction and proposals."""

    def __init__(self, name: str = "event"):
        super().__init__(name)
        self.api_key = os.getenv("NVIDIA_API_KEY")
        self.model = "meta/llama3-70b-instruct"
        self.api_url = "https://integrate.api.nvidia.com/v1/chat/completions"

    async def run(self, context: AgentContext) -> AgentResult:
        """Extract events from items and propose calendar actions."""
        start_time = time.time()

        try:
            items = [i for i in context.items if i.get("source_type") in ["email", "event"]]
            action_proposals = []

            for item in items:
                if item.get("source_type") == "email":
                    proposals = await self._extract_events_from_email(item)
                    action_proposals.extend(proposals)

            duration_ms = int((time.time() - start_time) * 1000)

            return self._create_result(
                status="success",
                output_summary={"items_processed": len(items), "events_proposed": len(action_proposals)},
                action_proposals=action_proposals,
                duration_ms=duration_ms,
            )

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            return self._create_result(status="error", error_message=str(e), duration_ms=duration_ms)

    async def _extract_events_from_email(self, item: Dict) -> List[Dict]:
        """Extract potential calendar events from email."""
        prompt = f"""Analyze this email and extract any calendar events or deadlines.

From: {item.get('sender', '')}
Subject: {item.get('title', '')}
Body: {item.get('body_full', '')[:2000]}

Respond with JSON array of events:
[
  {{
    "title": "Event title",
    "start": "YYYY-MM-DD HH:MM",
    "end": "YYYY-MM-DD HH:MM",
    "location": "location if mentioned",
    "description": "brief description",
    "event_type": "meeting|deadline|reminder"
  }}
]

Return empty array [] if no events found."""

        response = await self._call_llm(prompt)
        events = json.loads(response)

        proposals = []
        for event in events:
            proposal = {
                "agent_name": self.name,
                "action_type": "create_calendar_event",
                "related_item_id": item.get("id"),
                "payload": {
                    "title": event.get("title"),
                    "start": event.get("start"),
                    "end": event.get("end"),
                    "location": event.get("location", ""),
                    "description": event.get("description", ""),
                    "provider": "google_calendar",
                },
                "explanation": f"Create {event.get('event_type', 'event')} from email",
                "risk_level": "low",
            }
            proposals.append(proposal)

        return proposals

    async def _call_llm(self, prompt: str) -> str:
        """Call NVIDIA NIM API."""
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
            "max_tokens": 1024,
        }

        response = requests.post(self.api_url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
