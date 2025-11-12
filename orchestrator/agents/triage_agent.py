"""
Triage Agent - Classifies and prioritizes items.
"""

import json
import time
from datetime import datetime
from typing import Dict, List

from orchestrator.agents.base import AgentContext, AgentResult, BaseAgent
from orchestrator.llm_client import LLMClient


class TriageAgent(BaseAgent):
    """Agent that triages and categorizes items."""

    def __init__(self, name: str = "triage"):
        super().__init__(name)
        self.llm = LLMClient()

    async def run(self, context: AgentContext) -> AgentResult:
        """Triage items and generate metadata."""
        start_time = time.time()

        try:
            items = context.items
            if not items:
                return self._create_result(status="success", output_summary={"items_processed": 0}, duration_ms=0)

            metadata_updates = []
            for item in items:
                try:
                    metadata = await self._triage_item(item)
                    metadata_updates.append({"item_id": item.get("id"), "metadata": metadata})
                except Exception as e:
                    # Continue processing other items
                    continue

            duration_ms = int((time.time() - start_time) * 1000)

            return self._create_result(
                status="success",
                output_summary={
                    "items_processed": len(items),
                    "metadata_created": len(metadata_updates),
                },
                metadata_updates=metadata_updates,
                duration_ms=duration_ms,
            )

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            return self._create_result(status="error", error_message=str(e), duration_ms=duration_ms)

    async def _triage_item(self, item: Dict) -> Dict:
        """Triage a single item using LLM."""
        prompt = self._build_triage_prompt(item)

        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
            "top_p": 0.7,
            "max_tokens": 1024,
        }

        response = requests.post(self.api_url, headers=headers, json=payload)
        response.raise_for_status()

        result = response.json()
        content = result["choices"][0]["message"]["content"]

        # Parse JSON response
        metadata = json.loads(content)

        return {
            "category": metadata.get("category", "other"),
            "importance": metadata.get("importance", "medium"),
            "action_type": metadata.get("action_type", "none"),
            "due_datetime": metadata.get("due_datetime"),
            "confidence_score": metadata.get("confidence_score", 0.5),
            "labels": metadata.get("labels", []),
            "is_scam": False,  # Safety agent will set this
            "is_noise": metadata.get("importance") == "ignore",
            "summary": metadata.get("summary", ""),
        }

    def _build_triage_prompt(self, item: Dict) -> str:
        """Build prompt for triaging an item."""
        return f"""Analyze this email/event and provide structured triage information.

Title: {item.get('title', '')}
Sender: {item.get('sender', '')}
Body Preview: {item.get('body_preview', '')[:500]}
Source Type: {item.get('source_type', 'email')}

Respond with ONLY valid JSON in this exact format:
{{
  "category": "deadline|meeting|invite|admin|offer|scam|newsletter|fyi|other",
  "importance": "critical|high|medium|low|ignore",
  "action_type": "reply|attend|add_event|pay|read|none",
  "due_datetime": "YYYY-MM-DD HH:MM:SS or null",
  "confidence_score": 0.0-1.0,
  "labels": [
    {{"type": "course", "value": "CS101"}},
    {{"type": "money", "value": 50.00, "currency": "USD"}}
  ],
  "summary": "One sentence summary"
}}

Classification rules:
- deadline: Contains explicit deadlines or due dates
- meeting: Calendar events or meeting invitations
- invite: Social or event invitations
- admin: Administrative tasks, forms, registrations
- offer: Promotional content or offers
- newsletter: Regular newsletters or updates
- fyi: Informational only, no action needed
- other: Doesn't fit categories

Importance rules:
- critical: Urgent deadlines within 24 hours, important meetings
- high: Deadlines within week, important communications
- medium: Standard emails requiring attention
- low: Low priority but may need response
- ignore: Spam, newsletters, no action needed

Extract due dates from phrases like:
- "due by Friday"
- "deadline: March 15"
- "submit before noon"
- "meeting at 2pm tomorrow"

Be conservative: if unsure, use medium importance and provide low confidence score."""
