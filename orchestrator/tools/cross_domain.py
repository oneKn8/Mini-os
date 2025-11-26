"""
Cross-domain intelligence tools using entity linking.

These tools connect information across different data sources
to provide richer context and insights.
"""

import logging
from typing import Any, Dict, List, Optional

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from orchestrator.entity_linker import get_entity_linker, LinkedContext

logger = logging.getLogger(__name__)


class RelatedItemsResult(BaseModel):
    """Result from finding related items."""

    query: str = Field(description="The original query")
    entities_found: List[Dict[str, str]] = Field(default_factory=list, description="Entities extracted from the query")
    related_emails: List[Dict[str, Any]] = Field(
        default_factory=list, description="Emails related to the query entities"
    )
    related_events: List[Dict[str, Any]] = Field(
        default_factory=list, description="Events related to the query entities"
    )
    summary: str = Field(description="Summary of connections found")


class PersonContextResult(BaseModel):
    """Context gathered about a person."""

    person: str = Field(description="The person's name or email")
    emails_involving: int = Field(default=0, description="Number of emails involving this person")
    events_with: int = Field(default=0, description="Number of events with this person")
    recent_emails: List[Dict[str, Any]] = Field(default_factory=list, description="Recent emails from/to this person")
    upcoming_events: List[Dict[str, Any]] = Field(default_factory=list, description="Upcoming events with this person")
    topics: List[str] = Field(default_factory=list, description="Topics discussed with this person")
    summary: str = Field(description="Summary of interactions")


@tool
def find_related_items(query: str, include_emails: bool = True, include_events: bool = True) -> RelatedItemsResult:
    """
    Find items across emails and calendar related to a query.

    Use this to gather context from multiple data sources, such as:
    - Finding emails related to a meeting topic
    - Finding calendar events that match an email thread
    - Connecting information about a person or project

    Args:
        query: What to search for (e.g., "meeting with John", "Project Alpha", "tomorrow's presentation")
        include_emails: Whether to search emails
        include_events: Whether to search calendar events

    Returns:
        Related items from emails and calendar with explanations of connections
    """
    try:
        linker = get_entity_linker()

        # For this to work well, we need data indexed
        # In production, this would query the database
        # For now, we'll extract entities from the query and search the index

        context = linker.get_linked_context(
            query=query,
            emails=[],  # Would come from database
            events=[],  # Would come from database
            max_results=5,
        )

        return RelatedItemsResult(
            query=query,
            entities_found=[{"type": e["type"], "value": e["value"]} for e in context.query_entities],
            related_emails=context.related_emails if include_emails else [],
            related_events=context.related_events if include_events else [],
            summary=context.summary,
        )

    except Exception as e:
        logger.error(f"Error finding related items: {e}")
        return RelatedItemsResult(
            query=query,
            entities_found=[],
            related_emails=[],
            related_events=[],
            summary=f"Error searching: {str(e)}",
        )


@tool
def get_person_context(person: str) -> PersonContextResult:
    """
    Get full context about a person across all data sources.

    Use this when you need to gather information about someone, such as:
    - Preparing for a meeting with them
    - Finding your recent interactions
    - Understanding your relationship with them

    Args:
        person: The person's name or email address

    Returns:
        Comprehensive context including emails, events, and shared topics
    """
    try:
        linker = get_entity_linker()

        # Find all items involving this person
        person_entities = linker.find_by_person(person)

        # Count by type
        email_count = sum(1 for e in person_entities if e.source_type == "email")
        event_count = sum(1 for e in person_entities if e.source_type == "event")

        # In production, we would fetch the actual items from the database
        # For now, return a summary

        summary_parts = []
        if email_count > 0:
            summary_parts.append(f"{email_count} email{'s' if email_count > 1 else ''}")
        if event_count > 0:
            summary_parts.append(f"{event_count} event{'s' if event_count > 1 else ''}")

        if summary_parts:
            summary = f"Found {' and '.join(summary_parts)} involving {person}"
        else:
            summary = f"No recorded interactions with {person}"

        return PersonContextResult(
            person=person,
            emails_involving=email_count,
            events_with=event_count,
            recent_emails=[],  # Would be populated from database
            upcoming_events=[],  # Would be populated from database
            topics=[],  # Would extract from indexed data
            summary=summary,
        )

    except Exception as e:
        logger.error(f"Error getting person context: {e}")
        return PersonContextResult(
            person=person,
            summary=f"Error: {str(e)}",
        )


@tool
def prepare_for_meeting(meeting_title: str, attendees: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Prepare comprehensive context for an upcoming meeting.

    Gathers:
    - Recent emails from/about attendees
    - Related previous meetings
    - Key topics from past interactions
    - Any pending action items

    Args:
        meeting_title: The title/subject of the meeting
        attendees: Optional list of attendee names or emails

    Returns:
        Comprehensive preparation context for the meeting
    """
    try:
        linker = get_entity_linker()

        context = {
            "meeting": meeting_title,
            "attendees": attendees or [],
            "related_emails": [],
            "previous_meetings": [],
            "key_topics": [],
            "pending_items": [],
            "preparation_notes": "",
        }

        # Extract entities from meeting title
        title_entities = linker.extractor.extract_from_text(meeting_title, "query", "query")

        # Find related content
        for entity in title_entities:
            if entity.type == "person" or entity.type == "topic":
                matches = linker.find_by_entity(entity.type, entity.value)
                for match in matches[:3]:
                    if match.source_type == "email":
                        context["related_emails"].append(
                            {
                                "id": match.source_id,
                                "matched_on": entity.value,
                            }
                        )
                    elif match.source_type == "event":
                        context["previous_meetings"].append(
                            {
                                "id": match.source_id,
                                "matched_on": entity.value,
                            }
                        )

        # Process attendees
        if attendees:
            for attendee in attendees:
                person_matches = linker.find_by_person(attendee)
                context["key_topics"].extend(
                    [e.metadata.get("display_name", e.value) for e in person_matches if e.type == "topic"][:2]
                )

        # Generate preparation notes
        notes_parts = []
        if context["related_emails"]:
            notes_parts.append(f"Found {len(context['related_emails'])} related emails to review")
        if context["previous_meetings"]:
            notes_parts.append(f"You've had {len(context['previous_meetings'])} previous related meetings")
        if context["key_topics"]:
            notes_parts.append(f"Key topics: {', '.join(set(context['key_topics']))}")

        context["preparation_notes"] = ". ".join(notes_parts) if notes_parts else "No related context found"

        return context

    except Exception as e:
        logger.error(f"Error preparing for meeting: {e}")
        return {
            "meeting": meeting_title,
            "error": str(e),
            "preparation_notes": "Error gathering meeting context",
        }


# Export tools
CROSS_DOMAIN_TOOLS = [
    find_related_items,
    get_person_context,
    prepare_for_meeting,
]
