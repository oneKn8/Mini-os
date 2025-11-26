"""
Entity Linker - Cross-domain intelligence for connecting related information.

This module extracts and links entities across different data sources:
- People (names, email addresses)
- Projects (project names, keywords)
- Time references (dates, deadlines)
- Topics (shared keywords, subjects)

Examples of cross-domain connections:
- "Your meeting with Sarah is tomorrow - here are 3 related emails"
- "You mentioned the Johnson project - it's due Friday and you have 2 unread updates"
- "Rain forecast for your hiking trip Saturday"
"""

import logging
import re
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Set, Tuple

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# ============================================================================
# Entity Types
# ============================================================================


class EntityType:
    """Types of entities we extract and link."""

    PERSON = "person"
    PROJECT = "project"
    DATE = "date"
    TOPIC = "topic"
    LOCATION = "location"
    ORGANIZATION = "organization"


@dataclass
class Entity:
    """A single extracted entity."""

    type: str
    value: str
    normalized: str  # Normalized form for matching
    source_id: str  # ID of the item this came from
    source_type: str  # email, event, etc.
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EntityConnection:
    """A connection between two items via shared entities."""

    source_id: str
    target_id: str
    source_type: str
    target_type: str
    shared_entities: List[Entity]
    connection_strength: float  # 0-1, based on number and type of shared entities
    explanation: str


class LinkedContext(BaseModel):
    """Context gathered by linking entities across domains."""

    query_entities: List[Dict[str, Any]] = Field(default_factory=list, description="Entities extracted from the query")
    related_emails: List[Dict[str, Any]] = Field(default_factory=list, description="Emails related via entities")
    related_events: List[Dict[str, Any]] = Field(
        default_factory=list, description="Calendar events related via entities"
    )
    connections: List[Dict[str, Any]] = Field(default_factory=list, description="Explanation of connections found")
    summary: str = Field(default="", description="Natural language summary of connections")


# ============================================================================
# Entity Extraction
# ============================================================================


class EntityExtractor:
    """Extracts entities from text and structured data."""

    # Common name patterns
    NAME_PATTERN = re.compile(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b")

    # Email pattern
    EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")

    # Project/topic patterns (capitalized words or quoted strings)
    PROJECT_PATTERN = re.compile(
        r"\b(?:the\s+)?([A-Z][a-zA-Z0-9]*(?:\s+[A-Z][a-zA-Z0-9]*)*\s+(?:project|initiative|plan|proposal|report))\b",
        re.IGNORECASE,
    )

    # Date patterns
    DATE_PATTERNS = [
        (re.compile(r"\b(today)\b", re.IGNORECASE), "today"),
        (re.compile(r"\b(tomorrow)\b", re.IGNORECASE), "tomorrow"),
        (re.compile(r"\b(yesterday)\b", re.IGNORECASE), "yesterday"),
        (re.compile(r"\b(this\s+week)\b", re.IGNORECASE), "this_week"),
        (re.compile(r"\b(next\s+week)\b", re.IGNORECASE), "next_week"),
        (re.compile(r"\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b", re.IGNORECASE), "weekday"),
        (re.compile(r"\b(\d{1,2}/\d{1,2}/\d{2,4})\b"), "date"),
        (re.compile(r"\b(\d{4}-\d{2}-\d{2})\b"), "iso_date"),
    ]

    # Common stop words to exclude
    STOP_WORDS = {
        "the",
        "a",
        "an",
        "and",
        "or",
        "but",
        "in",
        "on",
        "at",
        "to",
        "for",
        "of",
        "with",
        "by",
        "from",
        "as",
        "is",
        "was",
        "are",
        "were",
        "been",
        "be",
        "have",
        "has",
        "had",
        "do",
        "does",
        "did",
        "will",
        "would",
        "could",
        "should",
        "may",
        "might",
        "must",
        "shall",
        "can",
        "need",
        "not",
        "no",
        "yes",
        "hi",
        "hello",
        "hey",
        "thanks",
        "thank",
        "please",
        "re",
        "fwd",
        "fw",
    }

    def extract_from_text(self, text: str, source_id: str, source_type: str) -> List[Entity]:
        """Extract entities from plain text."""
        entities = []

        if not text:
            return entities

        # Extract emails (often contain person names)
        for match in self.EMAIL_PATTERN.finditer(text):
            email = match.group()
            name_part = email.split("@")[0]
            # Try to extract name from email
            name = self._email_to_name(name_part)
            entities.append(
                Entity(
                    type=EntityType.PERSON,
                    value=email,
                    normalized=email.lower(),
                    source_id=source_id,
                    source_type=source_type,
                    metadata={"display_name": name},
                )
            )

        # Extract person names
        for match in self.NAME_PATTERN.finditer(text):
            name = match.group()
            # Skip if it's likely a title or common phrase
            if self._is_valid_name(name):
                entities.append(
                    Entity(
                        type=EntityType.PERSON,
                        value=name,
                        normalized=name.lower(),
                        source_id=source_id,
                        source_type=source_type,
                    )
                )

        # Extract projects
        for match in self.PROJECT_PATTERN.finditer(text):
            project = match.group(1)
            entities.append(
                Entity(
                    type=EntityType.PROJECT,
                    value=project,
                    normalized=project.lower(),
                    source_id=source_id,
                    source_type=source_type,
                )
            )

        # Extract date references
        for pattern, date_type in self.DATE_PATTERNS:
            for match in pattern.finditer(text):
                entities.append(
                    Entity(
                        type=EntityType.DATE,
                        value=match.group(),
                        normalized=match.group().lower(),
                        source_id=source_id,
                        source_type=source_type,
                        metadata={"date_type": date_type},
                    )
                )

        # Extract topics (significant capitalized words/phrases)
        topics = self._extract_topics(text)
        for topic in topics:
            entities.append(
                Entity(
                    type=EntityType.TOPIC,
                    value=topic,
                    normalized=topic.lower(),
                    source_id=source_id,
                    source_type=source_type,
                )
            )

        return entities

    def extract_from_email(self, email_data: Dict[str, Any], source_id: str) -> List[Entity]:
        """Extract entities from an email."""
        entities = []

        # Extract from sender
        sender = email_data.get("from", "")
        if sender:
            entities.extend(self.extract_from_text(sender, source_id, "email"))

        # Extract from recipients
        for recipient in email_data.get("to", []):
            entities.extend(self.extract_from_text(recipient, source_id, "email"))

        # Extract from subject
        subject = email_data.get("subject", "")
        if subject:
            entities.extend(self.extract_from_text(subject, source_id, "email"))

        # Extract from body (first 500 chars for efficiency)
        body = email_data.get("body", "")[:500]
        if body:
            entities.extend(self.extract_from_text(body, source_id, "email"))

        return self._deduplicate_entities(entities)

    def extract_from_event(self, event_data: Dict[str, Any], source_id: str) -> List[Entity]:
        """Extract entities from a calendar event."""
        entities = []

        # Extract from title/summary
        title = event_data.get("summary", event_data.get("title", ""))
        if title:
            entities.extend(self.extract_from_text(title, source_id, "event"))

        # Extract from description
        description = event_data.get("description", "")[:500]
        if description:
            entities.extend(self.extract_from_text(description, source_id, "event"))

        # Extract attendees
        for attendee in event_data.get("attendees", []):
            email = attendee.get("email", "")
            name = attendee.get("displayName", "")
            if email:
                entities.append(
                    Entity(
                        type=EntityType.PERSON,
                        value=email,
                        normalized=email.lower(),
                        source_id=source_id,
                        source_type="event",
                        metadata={"display_name": name},
                    )
                )
            if name and self._is_valid_name(name):
                entities.append(
                    Entity(
                        type=EntityType.PERSON,
                        value=name,
                        normalized=name.lower(),
                        source_id=source_id,
                        source_type="event",
                    )
                )

        # Extract location
        location = event_data.get("location", "")
        if location:
            entities.append(
                Entity(
                    type=EntityType.LOCATION,
                    value=location,
                    normalized=location.lower(),
                    source_id=source_id,
                    source_type="event",
                )
            )

        # Extract date from event
        start = event_data.get("start", {})
        start_time = start.get("dateTime", start.get("date", ""))
        if start_time:
            entities.append(
                Entity(
                    type=EntityType.DATE,
                    value=start_time,
                    normalized=start_time[:10] if len(start_time) >= 10 else start_time,
                    source_id=source_id,
                    source_type="event",
                    metadata={"is_event_date": True},
                )
            )

        return self._deduplicate_entities(entities)

    def _email_to_name(self, email_part: str) -> str:
        """Convert email local part to a name."""
        # Replace common separators
        name = email_part.replace(".", " ").replace("_", " ").replace("-", " ")
        # Capitalize words
        name = " ".join(word.capitalize() for word in name.split())
        return name

    def _is_valid_name(self, name: str) -> bool:
        """Check if a string looks like a valid person name."""
        words = name.split()
        if len(words) < 2 or len(words) > 4:
            return False

        # Check each word
        for word in words:
            if word.lower() in self.STOP_WORDS:
                return False
            if len(word) < 2:
                return False

        # Common false positives
        false_positives = {
            "project manager",
            "team lead",
            "vice president",
            "general manager",
            "product owner",
            "dear sir",
            "best regards",
            "kind regards",
            "thank you",
        }
        if name.lower() in false_positives:
            return False

        return True

    def _extract_topics(self, text: str) -> List[str]:
        """Extract significant topics from text."""
        topics = []

        # Look for capitalized phrases that might be topics
        words = text.split()
        current_topic = []

        for word in words:
            # Clean word
            clean_word = re.sub(r"[^\w]", "", word)

            if clean_word and clean_word[0].isupper() and clean_word.lower() not in self.STOP_WORDS:
                current_topic.append(clean_word)
            else:
                if len(current_topic) >= 2:
                    topic = " ".join(current_topic)
                    if len(topic) > 5:  # Minimum length
                        topics.append(topic)
                current_topic = []

        # Don't forget the last topic
        if len(current_topic) >= 2:
            topic = " ".join(current_topic)
            if len(topic) > 5:
                topics.append(topic)

        return topics[:5]  # Limit to top 5 topics

    def _deduplicate_entities(self, entities: List[Entity]) -> List[Entity]:
        """Remove duplicate entities."""
        seen = set()
        unique = []
        for entity in entities:
            key = (entity.type, entity.normalized)
            if key not in seen:
                seen.add(key)
                unique.append(entity)
        return unique


# ============================================================================
# Entity Linker
# ============================================================================


class EntityLinker:
    """
    Links entities across different data sources to find connections.

    This enables:
    - Finding emails related to calendar events
    - Finding events related to email threads
    - Connecting items via shared people, projects, topics
    """

    def __init__(self):
        """Initialize the entity linker."""
        self.extractor = EntityExtractor()
        # Entity index: type -> normalized -> list of entities
        self._entity_index: Dict[str, Dict[str, List[Entity]]] = defaultdict(lambda: defaultdict(list))
        # Item index: item_id -> list of entities
        self._item_index: Dict[str, List[Entity]] = defaultdict(list)

    def index_email(self, email_id: str, email_data: Dict[str, Any]) -> List[Entity]:
        """Index an email for entity linking."""
        entities = self.extractor.extract_from_email(email_data, email_id)
        self._add_to_index(email_id, entities)
        return entities

    def index_event(self, event_id: str, event_data: Dict[str, Any]) -> List[Entity]:
        """Index a calendar event for entity linking."""
        entities = self.extractor.extract_from_event(event_data, event_id)
        self._add_to_index(event_id, entities)
        return entities

    def index_item(self, item_id: str, item_data: Dict[str, Any], item_type: str) -> List[Entity]:
        """Index any item for entity linking."""
        if item_type == "email":
            return self.index_email(item_id, item_data)
        elif item_type == "event":
            return self.index_event(item_id, item_data)
        else:
            # Generic text extraction
            text = item_data.get("content", item_data.get("body", ""))
            entities = self.extractor.extract_from_text(text, item_id, item_type)
            self._add_to_index(item_id, entities)
            return entities

    def _add_to_index(self, item_id: str, entities: List[Entity]) -> None:
        """Add entities to the index."""
        self._item_index[item_id] = entities
        for entity in entities:
            self._entity_index[entity.type][entity.normalized].append(entity)

    def find_related_items(
        self, item_id: str, exclude_types: Optional[Set[str]] = None, min_strength: float = 0.3
    ) -> List[EntityConnection]:
        """Find items related to the given item via shared entities."""
        connections = []
        exclude_types = exclude_types or set()

        source_entities = self._item_index.get(item_id, [])
        if not source_entities:
            return []

        source_type = source_entities[0].source_type if source_entities else "unknown"

        # Find items sharing entities
        related_items: Dict[str, List[Entity]] = defaultdict(list)

        for entity in source_entities:
            matching = self._entity_index[entity.type].get(entity.normalized, [])
            for match in matching:
                if match.source_id != item_id and match.source_type not in exclude_types:
                    related_items[match.source_id].append(entity)

        # Create connections
        for target_id, shared in related_items.items():
            target_entities = self._item_index.get(target_id, [])
            target_type = target_entities[0].source_type if target_entities else "unknown"

            # Calculate connection strength
            strength = self._calculate_strength(shared, source_entities)

            if strength >= min_strength:
                connections.append(
                    EntityConnection(
                        source_id=item_id,
                        target_id=target_id,
                        source_type=source_type,
                        target_type=target_type,
                        shared_entities=shared,
                        connection_strength=strength,
                        explanation=self._explain_connection(shared),
                    )
                )

        # Sort by strength
        connections.sort(key=lambda c: c.connection_strength, reverse=True)
        return connections

    def find_by_entity(
        self, entity_type: str, entity_value: str, item_types: Optional[Set[str]] = None
    ) -> List[Entity]:
        """Find all items containing a specific entity."""
        normalized = entity_value.lower()
        matches = self._entity_index[entity_type].get(normalized, [])

        if item_types:
            matches = [m for m in matches if m.source_type in item_types]

        return matches

    def find_by_person(self, person: str, item_types: Optional[Set[str]] = None) -> List[Entity]:
        """Find all items involving a person."""
        return self.find_by_entity(EntityType.PERSON, person, item_types)

    def get_linked_context(
        self, query: str, emails: List[Dict[str, Any]], events: List[Dict[str, Any]], max_results: int = 5
    ) -> LinkedContext:
        """
        Get context for a query by linking entities across data sources.

        Args:
            query: The user's query
            emails: Available email data
            events: Available event data
            max_results: Maximum related items to return

        Returns:
            LinkedContext with related items and explanations
        """
        # Extract entities from query
        query_entities = self.extractor.extract_from_text(query, "query", "query")

        related_emails = []
        related_events = []
        connections = []

        # Index all items (if not already indexed)
        for email in emails:
            email_id = str(email.get("id", hash(str(email))))
            if email_id not in self._item_index:
                self.index_email(email_id, email)

        for event in events:
            event_id = str(event.get("id", hash(str(event))))
            if event_id not in self._item_index:
                self.index_event(event_id, event)

        # Find related items for each query entity
        seen_email_ids = set()
        seen_event_ids = set()

        for entity in query_entities:
            matches = self._entity_index[entity.type].get(entity.normalized, [])

            for match in matches:
                if match.source_type == "email" and match.source_id not in seen_email_ids:
                    # Find the email in our list
                    for email in emails:
                        if str(email.get("id", hash(str(email)))) == match.source_id:
                            related_emails.append(
                                {
                                    **email,
                                    "matched_entity": entity.value,
                                    "entity_type": entity.type,
                                }
                            )
                            seen_email_ids.add(match.source_id)
                            break

                elif match.source_type == "event" and match.source_id not in seen_event_ids:
                    # Find the event in our list
                    for event in events:
                        if str(event.get("id", hash(str(event)))) == match.source_id:
                            related_events.append(
                                {
                                    **event,
                                    "matched_entity": entity.value,
                                    "entity_type": entity.type,
                                }
                            )
                            seen_event_ids.add(match.source_id)
                            break

        # Limit results
        related_emails = related_emails[:max_results]
        related_events = related_events[:max_results]

        # Generate summary
        summary = self._generate_summary(query_entities, related_emails, related_events)

        return LinkedContext(
            query_entities=[{"type": e.type, "value": e.value, "normalized": e.normalized} for e in query_entities],
            related_emails=related_emails,
            related_events=related_events,
            connections=[
                {
                    "from": "query",
                    "to_type": e.source_type,
                    "via": e.type,
                    "entity": e.value,
                }
                for e in query_entities
                if self._entity_index[e.type].get(e.normalized)
            ],
            summary=summary,
        )

    def _calculate_strength(self, shared: List[Entity], total: List[Entity]) -> float:
        """Calculate connection strength based on shared entities."""
        if not total:
            return 0.0

        # Weight by entity type importance
        weights = {
            EntityType.PERSON: 1.5,
            EntityType.PROJECT: 1.3,
            EntityType.DATE: 1.0,
            EntityType.TOPIC: 0.8,
            EntityType.LOCATION: 0.7,
            EntityType.ORGANIZATION: 1.2,
        }

        shared_weight = sum(weights.get(e.type, 1.0) for e in shared)
        total_weight = sum(weights.get(e.type, 1.0) for e in total)

        # Normalize to 0-1
        return min(shared_weight / max(total_weight, 1.0), 1.0)

    def _explain_connection(self, shared: List[Entity]) -> str:
        """Generate a human-readable explanation of the connection."""
        if not shared:
            return "No direct connection"

        parts = []

        # Group by type
        by_type: Dict[str, List[Entity]] = defaultdict(list)
        for entity in shared:
            by_type[entity.type].append(entity)

        for entity_type, entities in by_type.items():
            values = [e.value for e in entities[:3]]  # Max 3 per type

            if entity_type == EntityType.PERSON:
                if len(values) == 1:
                    parts.append(f"involves {values[0]}")
                else:
                    parts.append(f"involves {', '.join(values)}")
            elif entity_type == EntityType.PROJECT:
                parts.append(f"about {', '.join(values)}")
            elif entity_type == EntityType.TOPIC:
                parts.append(f"discusses {', '.join(values)}")
            elif entity_type == EntityType.DATE:
                parts.append(f"on {', '.join(values)}")

        return "; ".join(parts) if parts else "Related via shared context"

    def _generate_summary(
        self, query_entities: List[Entity], related_emails: List[Dict], related_events: List[Dict]
    ) -> str:
        """Generate a natural language summary of found connections."""
        if not query_entities:
            return "No specific entities found in your query."

        parts = []

        # Summarize what we found
        entity_summary = []
        for entity in query_entities[:3]:
            if entity.type == EntityType.PERSON:
                entity_summary.append(f"person '{entity.value}'")
            elif entity.type == EntityType.PROJECT:
                entity_summary.append(f"project '{entity.value}'")
            elif entity.type == EntityType.TOPIC:
                entity_summary.append(f"topic '{entity.value}'")

        if entity_summary:
            parts.append(f"Looking for: {', '.join(entity_summary)}")

        if related_emails:
            parts.append(f"Found {len(related_emails)} related email{'s' if len(related_emails) > 1 else ''}")

        if related_events:
            parts.append(f"Found {len(related_events)} related event{'s' if len(related_events) > 1 else ''}")

        if not related_emails and not related_events:
            parts.append("No related items found")

        return ". ".join(parts)

    def clear_index(self) -> None:
        """Clear all indexed entities."""
        self._entity_index.clear()
        self._item_index.clear()


# ============================================================================
# Factory Functions
# ============================================================================


def create_entity_linker() -> EntityLinker:
    """Create an entity linker instance."""
    return EntityLinker()


# ============================================================================
# Singleton Instance
# ============================================================================

_entity_linker: Optional[EntityLinker] = None


def get_entity_linker() -> EntityLinker:
    """Get or create the singleton entity linker."""
    global _entity_linker
    if _entity_linker is None:
        _entity_linker = EntityLinker()
    return _entity_linker
