"""
Planner Agent - Generates daily and weekly plans.
"""

import json
import time
from datetime import datetime, timedelta
from typing import Dict, List

from orchestrator.agents.base import AgentContext, AgentResult, BaseAgent
from orchestrator.llm_client import LLMClient
from orchestrator.state import OpsAgentState


class PlannerAgent(BaseAgent):
    """Agent for daily and weekly planning. Works with LangGraph state."""

    def __init__(self, name: str = "planner"):
        super().__init__(name)
        self.llm = LLMClient()

    async def run(self, context: AgentContext | OpsAgentState) -> AgentResult:
        """Generate plan for today or upcoming days. Works with both AgentContext and OpsAgentState."""
        start_time = time.time()

        try:
            ctx = self._get_context(context)
            plan_summary = await self._generate_plan(ctx)
            action_proposals = await self._propose_time_blocks(ctx, plan_summary)

            duration_ms = int((time.time() - start_time) * 1000)

            # Return plan data directly (not nested) for chat compatibility
            return self._create_result(
                status="success",
                output_summary={
                    "must_do_today": plan_summary.get("must_do_today", []),
                    "focus_areas": plan_summary.get("focus_areas", []),
                    "time_recommendations": plan_summary.get("time_recommendations", []),
                    "time_blocks_proposed": len(action_proposals),
                },
                action_proposals=action_proposals,
                duration_ms=duration_ms,
            )

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            return self._create_result(status="error", error_message=str(e), duration_ms=duration_ms)

    async def _generate_plan(self, context: AgentContext) -> Dict:
        """Generate daily plan summary."""
        # Pass context to LLMClient if it needs to know provider/model preference
        self.llm = LLMClient(provider=context.model_provider, model=context.model_name)

        critical_items = [i for i in context.items if i.get("importance") in ["critical", "high"]]
        events = [i for i in context.items if i.get("source_type") == "event"]

        prompt = f"""Generate a focused daily plan based on these items.

Critical/High Priority Items ({len(critical_items)}):
{json.dumps([{'title': i.get('title'), 'due': i.get('due_datetime')} for i in critical_items[:10]], indent=2)}

Today's Events ({len(events)}):
{json.dumps([{'title': i.get('title'), 'start': str(i.get('start_datetime'))} for i in events[:5]], indent=2)}

Weather: {context.weather_context.get('condition', 'Clear')} {context.weather_context.get('temperature', 20)}°C

Respond with ONLY valid JSON (no markdown, no explanation):
{{
  "must_do_today": ["item 1", "item 2", "item 3"],
  "focus_areas": ["area 1", "area 2"],
  "time_recommendations": [
    {{"task": "task name", "suggested_time": "09:00", "duration_minutes": 60}}
  ]
}}

Keep it realistic - max 3-5 must-do items."""

        response = await self._call_llm(prompt)

        # Try to extract JSON from response
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            # Try to find JSON in the response
            import re

            json_match = re.search(r"\{[\s\S]*\}", response)
            if json_match:
                return json.loads(json_match.group())
            # Return a default plan if parsing fails
            return {
                "must_do_today": [item.get("title", "Task") for item in critical_items[:3]],
                "focus_areas": ["High priority tasks"],
                "time_recommendations": [],
            }

    async def _propose_time_blocks(self, context: AgentContext, plan: Dict) -> List[Dict]:
        """Propose calendar time blocks based on plan."""
        proposals = []
        now = datetime.now()

        for rec in plan.get("time_recommendations", [])[:3]:
            try:
                time_str = rec.get("suggested_time", "09:00")
                hour, minute = map(int, time_str.split(":"))
                start = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

                if start < now:
                    start += timedelta(days=1)

                end = start + timedelta(minutes=rec.get("duration_minutes", 60))

                proposal = {
                    "agent_name": self.name,
                    "action_type": "create_calendar_event",
                    "payload": {
                        "title": f"[Focus] {rec.get('task', 'Work block')}",
                        "start": start.isoformat(),
                        "end": end.isoformat(),
                        "description": "Planner-suggested time block",
                        "provider": "google_calendar",
                    },
                    "explanation": f"Planner suggests {rec.get('duration_minutes')}min block for {rec.get('task')}",
                    "risk_level": "low",
                }
                proposals.append(proposal)
            except Exception:
                continue

        return proposals

    async def _call_llm(self, prompt: str) -> str:
        """Call LLM API."""
        return self.llm.call(prompt, temperature=0.4, max_tokens=1024)
