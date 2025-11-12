"""
Planner Agent - Generates daily and weekly plans.
"""

import json
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List

import requests

from orchestrator.agents.base import AgentContext, AgentResult, BaseAgent


class PlannerAgent(BaseAgent):
    """Agent for daily and weekly planning."""

    def __init__(self, name: str = "planner"):
        super().__init__(name)
        self.api_key = os.getenv("NVIDIA_API_KEY")
        self.model = "meta/llama3-70b-instruct"
        self.api_url = "https://integrate.api.nvidia.com/v1/chat/completions"

    async def run(self, context: AgentContext) -> AgentResult:
        """Generate plan for today or upcoming days."""
        start_time = time.time()

        try:
            plan_summary = await self._generate_plan(context)
            action_proposals = await self._propose_time_blocks(context, plan_summary)

            duration_ms = int((time.time() - start_time) * 1000)

            return self._create_result(
                status="success",
                output_summary={"plan_summary": plan_summary, "time_blocks_proposed": len(action_proposals)},
                action_proposals=action_proposals,
                duration_ms=duration_ms,
            )

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            return self._create_result(status="error", error_message=str(e), duration_ms=duration_ms)

    async def _generate_plan(self, context: AgentContext) -> Dict:
        """Generate daily plan summary."""
        critical_items = [i for i in context.items if i.get("importance") in ["critical", "high"]]
        events = [i for i in context.items if i.get("source_type") == "event"]

        prompt = f"""Generate a focused daily plan.

Critical/High Priority Items ({len(critical_items)}):
{json.dumps([{'title': i.get('title'), 'due': i.get('due_datetime')} for i in critical_items[:10]], indent=2)}

Today's Events ({len(events)}):
{json.dumps([{'title': i.get('title'), 'start': str(i.get('start_datetime'))} for i in events[:5]], indent=2)}

Weather: {context.weather_context.get('condition', 'Clear')} {context.weather_context.get('temperature', 20)}°C

User Preferences:
- Quiet hours: {context.user_preferences.get('quiet_hours_start', 'none')} - {context.user_preferences.get('quiet_hours_end', 'none')}
- Work blocks: {context.user_preferences.get('preferred_work_blocks', [])}

Respond with JSON:
{{
  "must_do_today": ["item 1", "item 2", "item 3"],
  "focus_areas": ["area 1", "area 2"],
  "time_recommendations": [
    {{"task": "task", "suggested_time": "HH:MM", "duration_minutes": 60}}
  ]
}}

Keep it realistic - max 3-5 must-do items."""

        response = await self._call_llm(prompt)
        return json.loads(response)

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
            except:
                continue

        return proposals

    async def _call_llm(self, prompt: str) -> str:
        """Call NVIDIA NIM API."""
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.4,
            "max_tokens": 1024,
        }
        response = requests.post(self.api_url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
