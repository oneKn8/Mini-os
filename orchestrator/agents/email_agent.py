"""
Email Agent - Generates summaries and draft replies.
"""

import json
import time
from typing import Dict

from orchestrator.agents.base import AgentContext, AgentResult, BaseAgent
from orchestrator.llm_client import LLMClient


class EmailAgent(BaseAgent):
    """Agent for email summarization and draft generation."""

    def __init__(self, name: str = "email"):
        super().__init__(name)
        self.llm = LLMClient()

    async def run(self, context: AgentContext) -> AgentResult:
        """Generate email summaries and drafts."""
        start_time = time.time()

        try:
            items = [i for i in context.items if i.get("source_type") == "email"]
            metadata_updates = []
            action_proposals = []

            for item in items:
                summary = await self._summarize_email(item)
                metadata_updates.append({"item_id": item.get("id"), "metadata": {"summary": summary}})

                if context.metadata.get("draft_reply") and item.get("id") == context.metadata.get("item_id"):
                    draft = await self._generate_draft(item, context.user_preferences)
                    action_proposals.append(draft)

            duration_ms = int((time.time() - start_time) * 1000)

            return self._create_result(
                status="success",
                output_summary={"emails_processed": len(items), "drafts_created": len(action_proposals)},
                metadata_updates=metadata_updates,
                action_proposals=action_proposals,
                duration_ms=duration_ms,
            )

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            return self._create_result(status="error", error_message=str(e), duration_ms=duration_ms)

    async def _summarize_email(self, item: Dict) -> str:
        """Generate email summary."""
        prompt = f"""Summarize this email in 2-3 bullet points.

From: {item.get('sender', '')}
Subject: {item.get('title', '')}
Body: {item.get('body_preview', '')[:1000]}

Provide:
- TL;DR (one sentence)
- Key points (2-3 bullets)
- Required action (if any)

Be concise and actionable."""

        return await self._call_llm(prompt)

    async def _generate_draft(self, item: Dict, preferences: Dict) -> Dict:
        """Generate draft email reply."""
        tone = preferences.get("email_tone", "professional")

        prompt = f"""Generate a draft reply to this email.

Original Email:
From: {item.get('sender', '')}
Subject: {item.get('title', '')}
Body: {item.get('body_full', '')[:2000]}

Tone: {tone}
Instructions:
- Be {tone} and courteous
- Address main points
- Keep it concise
- Don't make commitments without user approval

Respond with JSON:
{{
  "subject": "Re: ...",
  "body": "draft email body"
}}"""

        response = await self._call_llm(prompt)
        draft_data = json.loads(response)

        return {
            "agent_name": self.name,
            "action_type": "create_email_draft",
            "related_item_id": item.get("id"),
            "payload": {
                "to": item.get("sender"),
                "subject": draft_data.get("subject"),
                "body": draft_data.get("body"),
                "provider": item.get("source_provider"),
            },
            "explanation": f"Draft reply in {tone} tone",
            "risk_level": "low",
        }

    async def _call_llm(self, prompt: str) -> str:
        """Call LLM API."""
        return self.llm.call(prompt, temperature=0.3, max_tokens=1024)
