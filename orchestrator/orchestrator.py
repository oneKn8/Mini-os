"""
Main orchestrator for multi-agent workflows.
"""

import time
from datetime import datetime
from typing import Dict, List

from sqlalchemy.orm import Session

from backend.api.models import AgentRunLog, Item, UserPreferences
from orchestrator.agents.base import AgentContext, AgentResult
from orchestrator.registry import registry


class Orchestrator:
    """Orchestrates multi-agent workflows."""

    def __init__(self, db: Session):
        self.db = db

    async def execute(self, user_id: str, intent: str, **kwargs) -> Dict:
        """
        Execute an orchestration intent.

        Args:
            user_id: User ID
            intent: Intent type (refresh_inbox, plan_day, handle_item)
            **kwargs: Additional parameters

        Returns:
            Execution summary
        """
        start_time = time.time()

        try:
            # Get user preferences
            preferences = self.db.query(UserPreferences).filter(UserPreferences.user_id == user_id).first()
            user_prefs = self._preferences_to_dict(preferences) if preferences else {}

            # Build context
            context = AgentContext(
                user_id=user_id,
                intent=intent,
                items=kwargs.get("items", []),
                user_preferences=user_prefs,
                weather_context=kwargs.get("weather_context", {}),
                metadata=kwargs,
            )

            # Determine which agents to run
            agents_to_run = self._get_agents_for_intent(intent)

            # Execute agents
            results = []
            for agent_name in agents_to_run:
                try:
                    agent_class = registry.get(agent_name)
                    agent = agent_class(agent_name)
                    result = await agent.run(context)
                    results.append(result)

                    # Log agent run
                    self._log_agent_run(user_id, agent_name, intent, result)

                    # Update context with results
                    if result.action_proposals:
                        context.action_proposals.extend(result.action_proposals)

                except Exception as e:
                    # Log error but continue
                    error_result = AgentResult(
                        agent_name=agent_name, status="error", error_message=str(e), duration_ms=0
                    )
                    results.append(error_result)
                    self._log_agent_run(user_id, agent_name, intent, error_result)

            duration_ms = int((time.time() - start_time) * 1000)

            return {
                "status": "success" if any(r.status == "success" for r in results) else "partial",
                "intent": intent,
                "agents_run": len(results),
                "successful": sum(1 for r in results if r.status == "success"),
                "failed": sum(1 for r in results if r.status == "error"),
                "action_proposals_created": sum(len(r.action_proposals) for r in results),
                "duration_ms": duration_ms,
                "results": [{"agent": r.agent_name, "status": r.status} for r in results],
            }

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            return {
                "status": "error",
                "intent": intent,
                "error": str(e),
                "duration_ms": duration_ms,
            }

    def _get_agents_for_intent(self, intent: str) -> List[str]:
        """Determine which agents to run for an intent."""
        agent_flows = {
            "refresh_inbox": ["triage", "safety", "email"],
            "plan_day": ["planner", "safety"],
            "handle_item": ["email", "event", "safety"],
            "draft_reply": ["email", "safety"],
        }

        return agent_flows.get(intent, [])

    def _log_agent_run(self, user_id: str, agent_name: str, context: str, result: AgentResult):
        """Log agent execution to database."""
        log = AgentRunLog(
            user_id=user_id,
            agent_name=agent_name,
            context=context,
            input_summary=result.output_summary.get("input", {}),
            output_summary=result.output_summary,
            status=result.status,
            error_message=result.error_message,
            duration_ms=result.duration_ms,
            completed_at=datetime.utcnow(),
        )
        self.db.add(log)
        self.db.commit()

    def _preferences_to_dict(self, preferences: UserPreferences) -> Dict:
        """Convert UserPreferences to dict."""
        return {
            "quiet_hours_start": preferences.quiet_hours_start,
            "quiet_hours_end": preferences.quiet_hours_end,
            "preferred_work_blocks": preferences.preferred_work_blocks or [],
            "email_tone": preferences.email_tone,
            "meeting_preferences": preferences.meeting_preferences or {},
            "auto_reject_high_risk": preferences.auto_reject_high_risk,
            "enable_safety_agent": preferences.enable_safety_agent,
        }
