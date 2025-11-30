"""
Analyze actual token usage across different query types.

This script measures real token consumption to determine optimal context budgets.
"""

import asyncio
from typing import Dict, List
import tiktoken

from orchestrator.prompts import CONVERSATIONAL_AGENT_SYSTEM


def count_tokens(text: str, model: str = "gpt-4") -> int:
    """Count tokens using tiktoken."""
    try:
        encoding = tiktoken.encoding_for_model(model)
        return len(encoding.encode(text))
    except Exception:
        # Fallback: rough estimate (1 token ≈ 4 chars)
        return len(text) // 4


def analyze_system_prompt() -> Dict:
    """Analyze system prompt token usage."""
    # Format with sample context
    formatted = CONVERSATIONAL_AGENT_SYSTEM.format(
        current_time="2024-01-15 10:30 AM",
        day_of_week="Monday",
        timezone="PST",
        location="San Francisco, CA"
    )

    tokens = count_tokens(formatted)

    return {
        "component": "System Prompt",
        "tokens": tokens,
        "chars": len(formatted),
        "lines": formatted.count('\n'),
    }


def analyze_conversation_history(messages: int = 10) -> Dict:
    """Analyze typical conversation history."""
    # Simulate conversation
    sample_history = []

    # User messages (avg 50 tokens each)
    for i in range(messages // 2):
        sample_history.append(f"User: What's on my calendar for today? Can you also check the weather?")

    # Assistant messages (avg 150 tokens each)
    for i in range(messages // 2):
        sample_history.append(
            f"Assistant: Looking at your calendar, you have 3 events today:\n"
            f"1. Team standup at 9am\n2. Client meeting at 2pm\n3. Review session at 4pm\n\n"
            f"The weather is sunny, 72°F - perfect for that lunchtime walk!"
        )

    history_text = "\n\n".join(sample_history)
    tokens = count_tokens(history_text)

    return {
        "component": f"Conversation History ({messages} messages)",
        "tokens": tokens,
        "chars": len(history_text),
        "avg_per_message": tokens // messages if messages > 0 else 0,
    }


def analyze_tool_schemas() -> Dict:
    """Analyze tool schemas size."""
    # Typical tool schema
    sample_schema = """
{
    "name": "get_todays_events",
    "description": "Get all events scheduled for today from the user's calendar",
    "parameters": {
        "type": "object",
        "properties": {
            "include_past": {"type": "boolean", "description": "Include past events"},
            "max_results": {"type": "integer", "description": "Maximum events to return"}
        }
    }
}
"""

    # We have ~15 tools
    num_tools = 15
    tokens_per_tool = count_tokens(sample_schema)
    total_tokens = tokens_per_tool * num_tools

    return {
        "component": f"Tool Schemas ({num_tools} tools)",
        "tokens": total_tokens,
        "tokens_per_tool": tokens_per_tool,
        "num_tools": num_tools,
    }


def analyze_user_context() -> Dict:
    """Analyze user context size."""
    sample_context = {
        "user_id": "123",
        "name": "John Doe",
        "email": "john@example.com",
        "timezone": "America/Los_Angeles",
        "preferences": {
            "work_hours": "9am-5pm",
            "focus_time": "morning",
            "notification_style": "minimal"
        }
    }

    import json
    context_text = json.dumps(sample_context, indent=2)
    tokens = count_tokens(context_text)

    return {
        "component": "User Context",
        "tokens": tokens,
        "chars": len(context_text),
    }


def analyze_tool_results() -> Dict:
    """Analyze typical tool result size."""
    sample_result = """
Tool: get_todays_events
Result: {
    "events": [
        {
            "id": "evt_1",
            "title": "Team Standup",
            "start": "2024-01-15T09:00:00",
            "end": "2024-01-15T09:30:00",
            "location": "Zoom",
            "attendees": ["alice@example.com", "bob@example.com"]
        },
        {
            "id": "evt_2",
            "title": "Client Meeting",
            "start": "2024-01-15T14:00:00",
            "end": "2024-01-15T15:00:00",
            "location": "Conference Room A"
        }
    ],
    "total": 2
}
"""

    tokens = count_tokens(sample_result)

    return {
        "component": "Tool Result (1 tool)",
        "tokens": tokens,
        "chars": len(sample_result),
    }


def main():
    """Analyze total token usage."""
    print("\n" + "="*60)
    print("TOKEN USAGE ANALYSIS")
    print("="*60 + "\n")

    components = [
        analyze_system_prompt(),
        analyze_conversation_history(10),
        analyze_tool_schemas(),
        analyze_user_context(),
        analyze_tool_results(),
    ]

    # Print breakdown
    total_tokens = 0
    for comp in components:
        tokens = comp['tokens']
        total_tokens += tokens
        print(f"{comp['component']:40} {tokens:>6} tokens")

        # Show additional details
        for key, value in comp.items():
            if key not in ['component', 'tokens']:
                print(f"  {key}: {value}")
        print()

    print("-" * 60)
    print(f"{'TOTAL (baseline query)':40} {total_tokens:>6} tokens\n")

    # Analyze different scenarios
    print("="*60)
    print("SCENARIO ANALYSIS")
    print("="*60 + "\n")

    scenarios = {
        "Simple greeting": {
            "system": 1,
            "history": 2,
            "tools": 0,
            "user_context": 0.5,
            "tool_results": 0,
        },
        "Single tool query": {
            "system": 1,
            "history": 0.5,
            "tools": 1,
            "user_context": 1,
            "tool_results": 1,
        },
        "Multi-tool query (3 tools)": {
            "system": 1,
            "history": 0.5,
            "tools": 1,
            "user_context": 1,
            "tool_results": 3,
        },
        "Complex conversation": {
            "system": 1,
            "history": 2,
            "tools": 1,
            "user_context": 1,
            "tool_results": 3,
        },
    }

    # Calculate scenario costs
    base_costs = {
        "system": components[0]['tokens'],
        "history": components[1]['tokens'],
        "tools": components[2]['tokens'],
        "user_context": components[3]['tokens'],
        "tool_results": components[4]['tokens'],
    }

    for scenario_name, multipliers in scenarios.items():
        scenario_total = sum(
            base_costs[comp] * mult
            for comp, mult in multipliers.items()
        )
        print(f"{scenario_name:30} {int(scenario_total):>6} tokens")

    print("\n" + "="*60)
    print("RECOMMENDATIONS")
    print("="*60 + "\n")

    # Calculate optimal budgets
    simple_tokens = int(sum(
        base_costs[comp] * scenarios["Simple greeting"][comp]
        for comp in base_costs
    ))

    multi_tool_tokens = int(sum(
        base_costs[comp] * scenarios["Multi-tool query (3 tools)"][comp]
        for comp in base_costs
    ))

    complex_tokens = int(sum(
        base_costs[comp] * scenarios["Complex conversation"][comp]
        for comp in base_costs
    ))

    print(f"1. Simple Queries (greetings, basic info):")
    print(f"   Current: ~{simple_tokens} tokens")
    print(f"   Optimal: ~{int(simple_tokens * 0.8)} tokens (minimal history, no tool schemas)")
    print()

    print(f"2. Multi-Tool Queries (main workload):")
    print(f"   Current: ~{multi_tool_tokens} tokens")
    print(f"   Optimal: ~{multi_tool_tokens} tokens (KEEP THIS - need full context)")
    print()

    print(f"3. Complex Conversations:")
    print(f"   Current: ~{complex_tokens} tokens")
    print(f"   Optimal: ~{int(complex_tokens * 0.9)} tokens (summarize old history)")
    print()

    print("KEY INSIGHTS:")
    print("-" * 60)
    print("✓ Most queries are multi-tool (need ~3000-4000 tokens)")
    print("✓ System prompt is necessary (don't reduce)")
    print("✓ Tool schemas are necessary (don't reduce)")
    print("✓ Main optimization: conversation history")
    print("  - Keep last 5 messages verbatim (~500 tokens)")
    print("  - Summarize older messages (~200 tokens)")
    print("✓ User context is small, keep it")
    print()
    print("RECOMMENDED STRATEGY:")
    print("-" * 60)
    print("• Simple queries: 1500-2000 tokens (reduce history)")
    print("• Multi-tool queries: 3000-4000 tokens (KEEP FULL CONTEXT)")
    print("• Complex queries: 4000-5000 tokens (light history compression)")
    print()
    print("⚠️  DON'T reduce below 3000 tokens for multi-tool queries")
    print("   → Agent needs full context to make smart decisions")
    print()


if __name__ == "__main__":
    main()
