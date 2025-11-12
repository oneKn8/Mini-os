"""
Preference Agent - Learns and updates user preferences.
"""

import json
import os
import time
from datetime import datetime
from typing import Dict, List

import requests

from orchestrator.agents.base import AgentContext, AgentResult, BaseAgent


class PreferenceAgent(BaseAgent):
    """Agent for learning user preferences from feedback signals."""

    def __init__(self, name: str = "preference"):
        super().__init__(name)
        self.api_key = os.getenv("NVIDIA_API_KEY")
        self.model = "meta/llama3-70b-instruct"
        self.api_url = "https://integrate.api.nvidia.com/v1/chat/completions"

    async def run(self, context: AgentContext) -> AgentResult:
        """Analyze feedback signals and update preferences."""
        start_time = time.time()

        try:
            signals = context.metadata.get("preference_signals", [])

            if not signals:
                return self._create_result(
                    status="success",
                    output_summary={"message": "No signals to process"},
                    duration_ms=int((time.time() - start_time) * 1000),
                )

            preference_updates = await self._analyze_signals(signals, context.user_preferences)

            duration_ms = int((time.time() - start_time) * 1000)

            return self._create_result(
                status="success",
                output_summary={"signals_processed": len(signals), "preferences_updated": len(preference_updates)},
                metadata_updates=[{"preference_updates": preference_updates}],
                duration_ms=duration_ms,
            )

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            return self._create_result(status="error", error_message=str(e), duration_ms=duration_ms)

    async def _analyze_signals(self, signals: List[Dict], current_prefs: Dict) -> Dict:
        """Analyze signals to identify preference patterns."""
        rejected_proposals = [s for s in signals if s.get("signal_type") == "reject_proposal"]
        approved_quickly = [
            s for s in signals if s.get("signal_type") == "approve_proposal" and s.get("response_time_ms", 0) < 5000
        ]
        marked_ignore = [s for s in signals if s.get("signal_type") == "mark_ignore"]

        prompt = f"""Analyze user feedback signals to update preferences.

Current Preferences:
{json.dumps(current_prefs, indent=2)}

Feedback Signals:
- Rejected proposals: {len(rejected_proposals)}
  Sample: {json.dumps(rejected_proposals[:3], indent=2)}

- Quickly approved: {len(approved_quickly)}
  Sample: {json.dumps(approved_quickly[:3], indent=2)}

- Marked as ignore: {len(marked_ignore)}
  Sample: {json.dumps(marked_ignore[:3], indent=2)}

Identify patterns and suggest preference updates:
- Email tone changes
- Quiet hour adjustments
- Category importance shifts
- Sender/domain filters
- Auto-approve rules

Respond with JSON:
{{
  "preference_updates": {{
    "key_to_update": "new_value",
    "another_key": {{"nested": "value"}}
  }},
  "reasoning": "Why these changes were suggested",
  "confidence": 0.0-1.0
}}

Only suggest updates with confidence > 0.6"""

        response = await self._call_llm(prompt)
        result = json.loads(response)

        if result.get("confidence", 0) > 0.6:
            return result.get("preference_updates", {})
        else:
            return {}

    async def _call_llm(self, prompt: str) -> str:
        """Call NVIDIA NIM API."""
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
            "max_tokens": 1024,
        }
        response = requests.post(self.api_url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
