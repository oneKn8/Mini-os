# Personal Ops Center - Database Schema

**Version:** 1.0  
**Date:** November 12, 2025  
**Status:** Phase 1 - Data Model Design

## Overview

This document defines the relational database schema for the Personal Ops Center. All tables use PostgreSQL 15+ features and are designed for normalization, performance, and scalability.

## Entity Relationship Diagram (Text)

```
User (1) ──< (N) ConnectedAccount
User (1) ──< (N) Item
User (1) ──< (N) ActionProposal
User (1) ──< (N) AgentRunLog
User (1) ──── (1) UserPreferences

Item (1) ──── (1) ItemAgentMetadata
Item (1) ──< (N) ActionProposal
Item (1) ──< (N) PreferenceSignal

ActionProposal (1) ──── (0..1) ExecutionLog
ActionProposal (1) ──< (N) PreferenceSignal
```

## Tables

### 1. users

Stores user account information.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY, DEFAULT uuid_generate_v4() | Unique user identifier |
| email | VARCHAR(255) | NOT NULL, UNIQUE | Primary email address |
| name | VARCHAR(255) | | User's full name |
| password_hash | VARCHAR(255) | NOT NULL | Hashed password (bcrypt) |
| timezone | VARCHAR(50) | DEFAULT 'UTC' | User's timezone (IANA format) |
| location_city | VARCHAR(100) | | City for weather |
| location_country | VARCHAR(100) | | Country for weather |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Account creation time |
| updated_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Last update time |
| is_active | BOOLEAN | DEFAULT true | Account active status |
| last_login_at | TIMESTAMP | | Last login timestamp |

**Indexes:**
- PRIMARY KEY on `id`
- UNIQUE INDEX on `email`
- INDEX on `is_active`

**Notes:**
- Password stored as bcrypt hash
- Timezone used for scheduling and display
- Location used for weather API

---

### 2. connected_accounts

Stores OAuth connections to external services.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY, DEFAULT uuid_generate_v4() | Unique account ID |
| user_id | UUID | NOT NULL, FOREIGN KEY → users(id) ON DELETE CASCADE | Owner user |
| provider | VARCHAR(50) | NOT NULL | gmail, outlook, google_calendar |
| provider_account_id | VARCHAR(255) | | Provider's account ID |
| provider_email | VARCHAR(255) | | Email at provider |
| access_token | TEXT | NOT NULL | Encrypted OAuth access token |
| refresh_token | TEXT | | Encrypted OAuth refresh token |
| token_expires_at | TIMESTAMP | | Token expiration time |
| scopes | JSONB | | Granted OAuth scopes |
| status | VARCHAR(50) | DEFAULT 'active' | active, expired, revoked, error |
| last_sync_at | TIMESTAMP | | Last successful sync |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Connection created |
| updated_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Last updated |

**Indexes:**
- PRIMARY KEY on `id`
- INDEX on `user_id`
- UNIQUE INDEX on `(user_id, provider, provider_account_id)` - One account per provider per user
- INDEX on `status`
- INDEX on `token_expires_at` for token refresh jobs

**Notes:**
- Tokens encrypted at rest using application-level encryption
- Multiple accounts of same provider allowed (e.g., 2 Gmail accounts)
- Status tracks OAuth health

---

### 3. items

Normalized storage for all ingested data (emails and events).

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY, DEFAULT uuid_generate_v4() | Unique item ID |
| user_id | UUID | NOT NULL, FOREIGN KEY → users(id) ON DELETE CASCADE | Owner user |
| source_type | VARCHAR(50) | NOT NULL | email, event |
| source_provider | VARCHAR(50) | NOT NULL | gmail, outlook, google_calendar |
| source_account_id | UUID | FOREIGN KEY → connected_accounts(id) ON DELETE SET NULL | Source account |
| source_id | VARCHAR(255) | NOT NULL | Provider's ID for the item |
| title | VARCHAR(500) | | Email subject or event title |
| body_preview | TEXT | | First ~500 chars |
| body_full | TEXT | | Full content (optional encryption) |
| sender | VARCHAR(255) | | Email sender or event organizer |
| recipients | JSONB | | List of recipients |
| start_datetime | TIMESTAMP | | Event start time |
| end_datetime | TIMESTAMP | | Event end time |
| received_datetime | TIMESTAMP | | Email received or event created |
| raw_metadata | JSONB | | Provider-specific metadata |
| is_archived | BOOLEAN | DEFAULT false | User archived flag |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Ingested at |
| updated_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Last updated |

**Indexes:**
- PRIMARY KEY on `id`
- INDEX on `user_id`
- INDEX on `(user_id, source_type, received_datetime DESC)` for timeline queries
- INDEX on `(user_id, is_archived)` for active items
- UNIQUE INDEX on `(user_id, source_provider, source_id)` to prevent duplicates
- INDEX on `received_datetime DESC` for sorting
- INDEX on `start_datetime` for event queries
- GIN INDEX on `raw_metadata` for JSONB queries

**Notes:**
- Both emails and calendar events stored here
- Normalized to avoid duplication
- Source ID prevents re-ingestion of same item

---

### 4. item_agent_metadata

Agent-generated metadata for each item.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| item_id | UUID | PRIMARY KEY, FOREIGN KEY → items(id) ON DELETE CASCADE | Associated item |
| category | VARCHAR(50) | | deadline, meeting, invite, admin, offer, scam, newsletter, fyi, other |
| importance | VARCHAR(50) | | critical, high, medium, low, ignore |
| action_type | VARCHAR(50) | | reply, attend, add_event, pay, read, none |
| due_datetime | TIMESTAMP | | Extracted deadline |
| confidence_score | FLOAT | CHECK (confidence_score BETWEEN 0 AND 1) | Agent confidence |
| labels | JSONB | | Array of extracted entities |
| is_scam | BOOLEAN | DEFAULT false | Safety Agent flag |
| is_noise | BOOLEAN | DEFAULT false | Low-value content |
| summary | TEXT | | Email Agent summary |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Metadata generated |
| updated_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Last updated by agent |

**Indexes:**
- PRIMARY KEY on `item_id`
- INDEX on `category`
- INDEX on `importance`
- INDEX on `due_datetime` for deadline views
- INDEX on `is_scam` for safety filtering
- GIN INDEX on `labels` for entity search

**Notes:**
- 1:1 relationship with items
- Updated by Triage, Email, and Safety agents
- Used for filtering and prioritization

---

### 5. action_proposals

Agent-proposed actions awaiting user approval.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY, DEFAULT uuid_generate_v4() | Unique proposal ID |
| user_id | UUID | NOT NULL, FOREIGN KEY → users(id) ON DELETE CASCADE | Owner user |
| related_item_id | UUID | FOREIGN KEY → items(id) ON DELETE SET NULL | Related email/event |
| agent_name | VARCHAR(100) | NOT NULL | Agent that created proposal |
| action_type | VARCHAR(100) | NOT NULL | create_email_draft, create_calendar_event, etc. |
| payload | JSONB | NOT NULL | Action-specific data |
| status | VARCHAR(50) | DEFAULT 'pending' | pending, approved, executed, rejected, failed, expired |
| risk_level | VARCHAR(50) | DEFAULT 'low' | low, medium, high |
| explanation | TEXT | | Why this action is proposed |
| warning_text | TEXT | | Safety Agent warnings |
| expires_at | TIMESTAMP | | Proposal expiration time |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Proposal created |
| updated_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Last status change |
| approved_at | TIMESTAMP | | User approval time |
| executed_at | TIMESTAMP | | Execution completion time |

**Indexes:**
- PRIMARY KEY on `id`
- INDEX on `user_id`
- INDEX on `(user_id, status)` for filtering
- INDEX on `related_item_id`
- INDEX on `expires_at` for cleanup jobs
- INDEX on `created_at DESC` for recent proposals
- GIN INDEX on `payload` for searching

**Notes:**
- Payload structure varies by action_type
- Status transitions: pending → approved → executed/failed
- Can be rejected at any stage
- Expiration prevents stale proposals

---

### 6. execution_logs

Logs of executed actions for debugging and auditing.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY, DEFAULT uuid_generate_v4() | Unique log ID |
| user_id | UUID | NOT NULL, FOREIGN KEY → users(id) ON DELETE CASCADE | Owner user |
| action_proposal_id | UUID | NOT NULL, FOREIGN KEY → action_proposals(id) ON DELETE CASCADE | Executed proposal |
| executor_status | VARCHAR(50) | NOT NULL | success, failure, partial |
| executor_error | TEXT | | Error message if failed |
| external_ids | JSONB | | Provider IDs (e.g., draft_id, event_id) |
| request_payload | JSONB | | What was sent to provider |
| response_payload | JSONB | | What provider returned |
| execution_duration_ms | INTEGER | | How long execution took |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Execution timestamp |

**Indexes:**
- PRIMARY KEY on `id`
- INDEX on `user_id`
- INDEX on `action_proposal_id`
- INDEX on `executor_status` for failure analysis
- INDEX on `created_at DESC` for recent logs

**Notes:**
- One log per execution attempt
- Useful for debugging failed actions
- External IDs used to track provider resources

---

### 7. user_preferences

User-specific preferences and settings.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| user_id | UUID | PRIMARY KEY, FOREIGN KEY → users(id) ON DELETE CASCADE | Owner user |
| quiet_hours_start | TIME | | Start of quiet hours |
| quiet_hours_end | TIME | | End of quiet hours |
| preferred_work_blocks | JSONB | | Array of {day, start, end} |
| email_tone | VARCHAR(50) | DEFAULT 'professional' | casual, friendly, professional, formal |
| meeting_preferences | JSONB | | Meeting scheduling preferences |
| auto_reject_high_risk | BOOLEAN | DEFAULT true | Auto-reject dangerous actions |
| enable_safety_agent | BOOLEAN | DEFAULT true | Run safety checks |
| enable_preference_learning | BOOLEAN | DEFAULT true | Learn from user behavior |
| notification_settings | JSONB | | Notification preferences |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Preferences created |
| updated_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Last updated |

**Indexes:**
- PRIMARY KEY on `user_id`
- GIN INDEX on `preferred_work_blocks`

**Notes:**
- 1:1 relationship with users
- Updated by Preference Agent based on signals
- Used by Planner and Email agents

---

### 8. preference_signals

Tracks user interactions for learning preferences.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY, DEFAULT uuid_generate_v4() | Unique signal ID |
| user_id | UUID | NOT NULL, FOREIGN KEY → users(id) ON DELETE CASCADE | Owner user |
| item_id | UUID | FOREIGN KEY → items(id) ON DELETE SET NULL | Related item |
| action_proposal_id | UUID | FOREIGN KEY → action_proposals(id) ON DELETE SET NULL | Related proposal |
| signal_type | VARCHAR(50) | NOT NULL | approved, rejected, ignored, edited_heavily, edited_lightly |
| context | JSONB | | Additional context (e.g., edit diff) |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Signal timestamp |

**Indexes:**
- PRIMARY KEY on `id`
- INDEX on `user_id`
- INDEX on `(user_id, signal_type)` for aggregation
- INDEX on `action_proposal_id`
- INDEX on `created_at DESC` for recent signals

**Notes:**
- Captured on every user interaction
- Used by Preference Agent to learn patterns
- Drives personalization

---

### 9. agent_run_logs

Logs of orchestrator and agent executions.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY, DEFAULT uuid_generate_v4() | Unique run ID |
| user_id | UUID | NOT NULL, FOREIGN KEY → users(id) ON DELETE CASCADE | Owner user |
| agent_name | VARCHAR(100) | NOT NULL | orchestrator, triage, email, etc. |
| context | VARCHAR(100) | NOT NULL | refresh_inbox, plan_day, handle_item, etc. |
| input_summary | JSONB | | Summary of input data |
| output_summary | JSONB | | Summary of outputs |
| status | VARCHAR(50) | NOT NULL | success, partial, error |
| error_message | TEXT | | Error details if failed |
| duration_ms | INTEGER | | Execution time |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Run started |
| completed_at | TIMESTAMP | | Run completed |

**Indexes:**
- PRIMARY KEY on `id`
- INDEX on `user_id`
- INDEX on `(user_id, agent_name, created_at DESC)` for agent history
- INDEX on `status` for failure analysis
- INDEX on `created_at DESC` for recent logs

**Notes:**
- One entry per agent execution
- Used for debugging and monitoring
- Visible in Agent Console UI

---

## Data Types Reference

### Enums (Enforced at Application Level)

**source_type:**
- email
- event

**source_provider:**
- gmail
- outlook
- google_calendar

**category:**
- deadline
- meeting
- invite
- admin
- offer
- scam
- newsletter
- fyi
- other

**importance:**
- critical
- high
- medium
- low
- ignore

**action_type (item level):**
- reply
- attend
- add_event
- pay
- read
- none

**action_type (proposal level):**
- create_email_draft
- create_calendar_event
- update_calendar_event
- delete_calendar_event
- create_reminder_event

**status (connected_accounts):**
- active
- expired
- revoked
- error

**status (action_proposals):**
- pending
- approved
- executed
- rejected
- failed
- expired

**risk_level:**
- low
- medium
- high

**signal_type:**
- approved
- rejected
- ignored
- edited_heavily
- edited_lightly

**executor_status:**
- success
- failure
- partial

**agent_run_status:**
- success
- partial
- error

## JSONB Column Structures

### items.recipients
```json
["email1@example.com", "email2@example.com"]
```

### items.raw_metadata
```json
{
  "gmail": {
    "message_id": "...",
    "thread_id": "...",
    "labels": ["INBOX", "UNREAD"]
  },
  "outlook": {
    "conversation_id": "...",
    "categories": ["Work"]
  },
  "google_calendar": {
    "event_id": "...",
    "recurrence": ["RRULE:FREQ=WEEKLY"]
  }
}
```

### item_agent_metadata.labels
```json
[
  {"type": "course", "value": "CS101"},
  {"type": "money", "value": 50.00, "currency": "USD"},
  {"type": "department", "value": "Registrar"}
]
```

### action_proposals.payload (create_email_draft)
```json
{
  "to": ["recipient@example.com"],
  "cc": [],
  "subject": "Re: Your request",
  "body": "Email content...",
  "provider": "gmail"
}
```

### action_proposals.payload (create_calendar_event)
```json
{
  "title": "Study Session - CS101",
  "start": "2025-11-15T14:00:00Z",
  "end": "2025-11-15T16:00:00Z",
  "location": "Library",
  "description": "Prepare for midterm",
  "provider": "google_calendar"
}
```

### user_preferences.preferred_work_blocks
```json
[
  {"day": "monday", "start": "09:00", "end": "12:00"},
  {"day": "monday", "start": "14:00", "end": "17:00"}
]
```

### user_preferences.meeting_preferences
```json
{
  "min_duration_minutes": 15,
  "max_duration_minutes": 120,
  "buffer_before_minutes": 5,
  "buffer_after_minutes": 5,
  "avoid_lunch_hours": true
}
```

## Database Setup Script

```sql
-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Set timezone
SET timezone = 'UTC';

-- Create tables in dependency order
-- (See individual CREATE TABLE statements in implementation)
```

## Migration Strategy

Using Alembic for migrations:

1. Initial migration: Create all tables
2. Future migrations: Add indexes, constraints, columns
3. Data migrations: Handled separately with scripts

## Performance Considerations

### Query Patterns

**Most Common Queries:**
1. Get user's unarchived items (needs: user_id + is_archived index)
2. Get pending action proposals (needs: user_id + status index)
3. Get recent agent runs (needs: user_id + created_at index)
4. Get items by due date (needs: item_agent_metadata.due_datetime index)

### Index Strategy

- Composite indexes on (user_id, frequently_filtered_column)
- DESC indexes on timestamp columns for reverse chronological
- GIN indexes on JSONB for metadata queries
- Partial indexes for common filtered queries

### Partitioning (Future)

Consider partitioning for large tables:
- `items` by `received_datetime` (monthly partitions)
- `agent_run_logs` by `created_at` (weekly partitions)
- `execution_logs` by `created_at` (weekly partitions)

## Backup & Retention

**Backup Strategy:**
- Daily full backups
- Point-in-time recovery enabled
- 30-day retention

**Data Retention:**
- Items: Keep forever (user controls via archive)
- Action Proposals: Keep 90 days after execution
- Execution Logs: Keep 90 days
- Agent Run Logs: Keep 30 days
- Preference Signals: Keep 1 year

---

**Database Schema Status:** ✅ Phase 1 Complete - Ready for Implementation

