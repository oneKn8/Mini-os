"""
Event Agent - Extracts and proposes calendar events.
"""

import json
import time
from datetime import datetime, timedelta
from typing import Dict, List

from orchestrator.agents.base import AgentContext, AgentResult, BaseAgent
from orchestrator.llm_client import LLMClient


class EventAgent(BaseAgent):
    """Agent for calendar event extraction and proposals."""

    def __init__(self, name: str = "event"):
        super().__init__(name)
        self.llm = LLMClient()

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
        """Call LLM API."""
        return self.llm.call(prompt, temperature=0.2, max_tokens=1024)
