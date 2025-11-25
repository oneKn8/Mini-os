"""
Safety Agent - Detects scams and assesses action risk.
"""

import json
import time
from typing import Dict

from orchestrator.agents.base import AgentContext, AgentResult, BaseAgent
from orchestrator.llm_client import LLMClient
from orchestrator.state import OpsAgentState


class SafetyAgent(BaseAgent):
    """Agent for safety checking and scam detection. Works with LangGraph state."""

    def __init__(self, name: str = "safety"):
        super().__init__(name)
        self.llm = LLMClient()

    async def run(self, context: AgentContext | OpsAgentState) -> AgentResult:
        """Check items for scams and assess action risks. Works with both AgentContext and OpsAgentState."""
        start_time = time.time()

        try:
            ctx = self._get_context(context)
            metadata_updates = []
            proposal_updates = []

            for item in ctx.items:
                if item.get("source_type") == "email":
                    safety_check = await self._check_email_safety(item)
                    metadata_updates.append({"item_id": item.get("id"), "metadata": safety_check})

            for proposal in ctx.action_proposals:
                risk = await self._assess_action_risk(proposal)
                proposal_updates.append({"proposal_id": proposal.get("id"), "risk": risk})

            duration_ms = int((time.time() - start_time) * 1000)

            return self._create_result(
                status="success",
                output_summary={
                    "emails_checked": len([i for i in context.items if i.get("source_type") == "email"]),
                    "scams_detected": sum(1 for m in metadata_updates if m["metadata"].get("is_scam")),
                    "proposals_assessed": len(proposal_updates),
                },
                metadata_updates=metadata_updates,
                duration_ms=duration_ms,
            )

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            return self._create_result(status="error", error_message=str(e), duration_ms=duration_ms)

    async def _check_email_safety(self, item: Dict) -> Dict:
        """Check email for phishing/scam patterns."""
        prompt = f"""Analyze this email for safety concerns.

From: {item.get('sender', '')}
Subject: {item.get('title', '')}
Body: {item.get('body_preview', '')[:1000]}

Check for:
- Phishing attempts
- Fake login requests
- Money transfer scams
- Suspicious links
- Urgent/threatening language
- Impersonation

Respond with JSON:
{{
  "is_scam": true/false,
  "safety_label": "safe|suspicious|dangerous",
  "concerns": ["concern 1", "concern 2"],
  "confidence": 0.0-1.0
}}"""

        response = await self._call_llm(prompt)
        result = json.loads(response)

        return {"is_scam": result.get("is_scam", False), "safety_concerns": result.get("concerns", [])}

    async def _assess_action_risk(self, proposal: Dict) -> Dict:
        """Assess risk level of an action proposal."""
        action_type = proposal.get("action_type", "")

        high_risk_actions = ["delete_calendar_event", "forward_email", "send_email"]
        medium_risk_actions = ["create_calendar_event", "update_calendar_event"]

        if action_type in high_risk_actions:
            risk_level = "high"
            warning = "This action will modify external data"
        elif action_type in medium_risk_actions:
            risk_level = "medium"
            warning = "This action will create or update data"
        else:
            risk_level = "low"
            warning = None

        return {"risk_level": risk_level, "warning_text": warning}

    async def _call_llm(self, prompt: str) -> str:
        """Call LLM API."""
        return self.llm.call(prompt, temperature=0.1, max_tokens=512)
