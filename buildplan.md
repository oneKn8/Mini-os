# Multi-Agent Personal Ops Center — Phased Build Plan

Smart personal “ops center” that watches Gmail, Outlook, Calendar, and weather, then proposes drafts and plans — but never does anything without your approval.

All phases are written as **build prompts** you can paste into Cursor / Claude Code / your dev agent.  
No timelines, just ordered phases. You can blitz through as fast as you want.

---

## 0. Project Framing & Architecture

**Goal:** Lock in architecture, responsibilities, and boundaries so the system doesn’t turn into spaghetti later.

### Outcomes

- Clear definition of:
  - Frontend app
  - Backend API
  - AI orchestration layer (multi-agent “brain”)
  - Data models: `User`, `ConnectedAccount`, `Item`, `ActionProposal`, `Preferences`, `AgentRunLog`
- Agreement on **contract**:  
  Agents only produce **structured proposals**; executor is the only thing that talks to Gmail/Outlook/Calendar.

### Core Concepts to Fix

- **Sources:**
  - Gmail (personal)
  - Outlook/Office 365 (school)
  - Google Calendar
  - Weather API for the user’s location
- **Capabilities:**
  - Summarize + triage emails
  - Extract deadlines, invites, tasks
  - Draft replies → save as drafts only
  - Propose calendar events/blocks/changes
  - Build “Today / Next few days” plan using calendar + weather
  - All external changes go through **Action Proposals → user approval → executor**

---

### AI Build Prompt — Phase 0 (Framing)

“Help me design a high-level architecture for a webapp called **Personal Ops Center**:

- Frontend: modern SPA, clean minimal UI with Inbox, Today, Planner, Agent Console, Settings.
- Backend: API for auth, OAuth integrations (Gmail, Outlook, Google Calendar), data ingestion, action execution.
- AI orchestration layer: separate concern that runs a **multi-agent workflow** (orchestrator + specialist agents) and writes all outputs into the database.
- Strict rule: AI agents **never** call Gmail/Outlook/Calendar directly. They only create structured `ActionProposal` records; a small deterministic executor applies them after user approval.
- Define at a conceptual level (no code):
  - Which services exist
  - Each service’s responsibilities
  - How they communicate (HTTP/JSON, queues, etc.)
  - Where multi-agent orchestration sits
  - How to represent agents’ inputs/outputs in a DB-friendly way.
- Summarize the design as diagrams in text form and bullet lists I can keep in my repo as architecture notes.”

---

## 1. Data Model & Storage Design

**Goal:** Design all core tables/entities up front so all agents and UI can rely on a stable shape.

### Required Entities

1. **User**
   - `id`, `primary_email`, `name`, `timezone`, `location_city`, `location_country`
2. **ConnectedAccount**
   - `id`, `user_id`, `provider` (gmail/outlook/google_calendar), tokens, scopes, status
3. **Item** (normalized input: email or event)
   - `id`, `user_id`, `source_type` (email/event), `source_provider` (gmail/outlook/google_calendar)
   - `source_id` (provider id), `title`, `body_preview`, `body_full` (optional separate table)
   - `sender`, `recipients`, `start_datetime`, `end_datetime`, `received_datetime`
   - `raw_metadata` (JSON)
4. **ItemAgentMetadata**
   - `item_id`
   - `category`, `importance`, `action_type`
   - `due_datetime`, `confidence_score`
   - `labels` (JSON array)
   - `is_scam`, `is_noise`
5. **ActionProposal**
   - `id`, `user_id`, `related_item_id`
   - `agent_name`, `action_type`
   - `payload` (JSON)
   - `status` (pending/approved/executed/rejected/failed)
   - `risk_level` (low/medium/high), `explanation`
   - timestamps
6. **ExecutionLog**
   - `id`, `user_id`, `action_proposal_id`
   - `executor_status`, `executor_error`, `external_ids` (JSON)
7. **UserPreferences**
   - `user_id`
   - `quiet_hours`, `preferred_work_blocks`, `email_tone`
   - `meeting_preferences`
   - other knobs
8. **PreferenceSignal**
   - `id`, `user_id`, `item_id`, `action_proposal_id`
   - `signal_type` (approved/rejected/ignored/edited_heavily)
   - timestamp
9. **AgentRunLog**
   - `id`, `user_id`, `agent_name`
   - `context` (refresh_inbox, plan_day, handle_item, etc.)
   - `input_summary`, `output_summary`
   - `status` (success/partial/error), `error_message`
   - timestamps

---

### AI Build Prompt — Phase 1 (Data Model)

“Design a relational data model for the Personal Ops Center with the following entities:

- User
- ConnectedAccount
- Item
- ItemAgentMetadata
- ActionProposal
- ExecutionLog
- UserPreferences
- PreferenceSignal
- AgentRunLog

For each table, specify:
- Columns + types
- Primary keys and foreign keys
- Indexes that are likely needed for performance (e.g., user_id + status)
- Any useful constraints (e.g., uniqueness on connected account per provider).

Do not write any SQL or ORM code, just the schema as structured descriptions. Organize it in a way I can paste into a design doc.”

---

## 2. Provider Integrations & Ingestion

**Goal:** Robustly ingest real data from Gmail, Outlook, Calendar, and Weather into `Item`s. No AI yet.

### Responsibilities

- OAuth flows for:
  - Gmail
  - Outlook/Office 365
  - Google Calendar
- Simple Weather API integration using user’s location.
- Periodic / on-demand sync:
  - Fetch:
    - Last N emails from Gmail + Outlook
    - Next 7–14 days of events from Google Calendar
  - Normalize into `Item`s
  - Store weather forecast in a separate internal structure for Planner Agent.

---

### AI Build Prompt — Phase 2 (Integrations & Ingestion)

“Help me design the ingestion layer for Personal Ops Center:

- I need OAuth-based integrations for:
  - Gmail (read emails, create drafts)
  - Outlook/Office 365 (read emails, create drafts)
  - Google Calendar (read events, create/update/delete events)
- I also need a Weather integration to fetch forecast for the user’s city for the next 3–7 days.

Describe in detail:

1. How to structure the **ingestion service**:
   - Endpoints for manual refresh (user clicks ‘Refresh’)
   - Background jobs (optional later) for periodic sync
   - How to use access/refresh tokens safely
   - How to only pull new/changed emails and events

2. How to normalize provider data into the `Item` schema:
   - For Gmail and Outlook emails
   - For Google Calendar events
   - How to handle partial/full bodies

3. How to represent and store weather data in a way the Planner Agent can consume later.

Keep it architectural and step-by-step, no actual code. Include edge cases I should watch for (rate limits, pagination, token expiration).”

---

## 3. Multi-Agent Orchestration Skeleton

**Goal:** Define the multi-agent “brain” shell: orchestrator + agent registry + basic run logging, with no fancy logic yet.

### Components

- **Orchestrator**
  - Receives high-level intents: `refresh_inbox`, `plan_day`, `handle_item`, etc.
  - Knows which agents to run and in what order.
  - Writes `AgentRunLog` entries.
- **Agent interface**
  - Common contract:
    - Input: user context + relevant IDs
    - Output: structured result (no side effects)
- **Agent registry**
  - Maps agent names to implementations.
- Initial stub agents:
  - `TriageAgent` (no real logic yet)
  - `EmailAgent` (summary + draft placeholder)
  - `PlannerAgent` (dummy)
  - `SafetyAgent` (dummy)
  - `PreferenceAgent` (dummy)

---

### AI Build Prompt — Phase 3 (Orchestrator Skeleton)

“Design the multi-agent orchestration framework for Personal Ops Center:

- I want an **Orchestrator** that:
  - Receives high-level intents like `refresh_inbox`, `plan_day`, `handle_item(item_id)`.
  - Decides which agents to run and in what sequence.
  - Passes a `context` object (user_id, mode, relevant item ids) into each agent.
  - Collects outputs from agents and writes them into the database (e.g., Item metadata, ActionProposal records).
  - Logs each agent run to an `AgentRunLog`.

- I want a simple **agent interface**, for example conceptually:
  - `run(context) -> AgentResult`
  - No direct I/O or external API calls from agents except through well-defined helper layers.

- I want an **agent registry**:
  - Map agent names to implementations.
  - Allow Orchestrator to call agents by name.
  - Easy to extend with new agents later.

Implement:
- The Orchestrator class with error handling
- The agent interface (BaseAgent abstract class)
- Agent registry
- Example flows for refresh_inbox, plan_day, handle_item"

---

## 4. Inbox Triage Agent (Signal Detector)

**Goal:** Turn raw `Item`s into categorized, prioritized, actionable entries.

### Responsibilities

- For each new/updated `Item`:
  - Classify:
    - `category`: deadline | meeting | invite | admin | offer | scam | newsletter | fyi | other
    - `importance`: critical | high | medium | low | ignore
    - `action_type`: reply | attend | add_event | pay | read | none
  - Extract:
    - `due_datetime` if text mentions deadlines
    - Entities: class codes, money amounts, departments, system names, etc.
  - Set `confidence_score`.
- Persist results in `ItemAgentMetadata`.

---

### AI Build Prompt — Phase 4 (Triage Agent)

“Design the **Inbox Triage Agent** for Personal Ops Center.

The agent will receive:
- A list of `Item` records (emails and events) for a user.
- Each `Item` has normalized fields like title, body_preview, body_full, sender, etc.

For each `Item`, the agent must:
- Decide:
  - `category` from {deadline, meeting, invite, admin, offer, scam, newsletter, fyi, other}
  - `importance` from {critical, high, medium, low, ignore}
  - `action_type` from {reply, attend, add_event, pay, read, none}
- Attempt to extract:
  - Any explicit or implied `due_datetime` in normalized form.
  - Important entities (course codes, money amounts, university departments, etc.).
- Assign a `confidence_score`.

Implement:
- TriageAgent class with LLM integration
- JSON-constrained output parsing
- Ambiguous case handling
- Orchestrator integration
- Database writes for ItemAgentMetadata

---

## 5. Specialist Agents: Email, Events, Weather Context

**Goal:** Add specialist agents that handle email content, calendar interactions, and weather context.

### 5.1 Email Summary & Draft Agent

Responsibilities:

- Summarize important emails:
  - TL;DR (1 line)
  - 2–3 bullet summary
- Extract:
  - Ask/required action
  - Any hidden deadlines
- Draft replies on request:
  - Respect `UserPreferences.email_tone`
  - Generate structured reply (to, subject, body) for **drafts only**

### 5.2 Event & Invite Agent

Responsibilities:

- For items classified as meeting/invite/deadline:
  - Extract event title, start/end, location/link.
  - Propose:
    - `create_calendar_event`
    - `update_calendar_event`
    - `create_reminder_event` (study block, leave buffer)
- Link proposals back to source `Item` where relevant.

### 5.3 Weather Context Agent

Responsibilities:

- Take weather forecast and upcoming events.
- Tag timeslots/events with:
  - `ok_for_outdoor`, `avoid_travel`, `neutral`, etc.
- Provide simple context features for the Planner Agent:
  - “Heavy rain during this window”, etc.

---

### AI Build Prompt — Phase 5 (Specialist Agents)

“Design three specialist agents for Personal Ops Center:

1. **Email Summary & Draft Agent**
   - Input: item ids for important emails, and user preferences (email tone).
   - For each email:
     - Produce a TL;DR and 2–3 bullet summary.
     - Extract what the sender wants or what the user is expected to do.
   - On user request for a specific email:
     - Generate a structured reply draft (to, subject, body), respecting `UserPreferences.email_tone`.
     - The output must be a JSON blob suitable for an `ActionProposal` of type `create_email_draft`.

2. **Event & Invite Agent**
   - Input: item ids where `category` is meeting/invite/deadline.
   - Extract structured event details (summary, start, end, location/link).
   - Propose calendar actions:
     - `create_calendar_event`
     - `update_calendar_event`
     - `create_reminder_event` for study time or buffer travel time.
   - Output = list of structured action proposals.

3. **Weather Context Agent**
   - Input: weather forecast (time-bucketed) + upcoming events.
   - Output:
     - Simple tags/annotations on time ranges and events like `ok_for_outdoor`, `avoid_travel`, `heavy_rain`, etc.
   - These annotations should be stored in a way the Planner Agent can consume easily.

Implement all three specialist agents with:
- Input/output structures
- LLM integration
- Action proposal generation
- Orchestrator integration"

---

## 6. Planner Agent (Today & Next Few Days)

**Goal:** Turn triaged items + calendar + weather into a small, focused plan and scheduling proposals.

### Responsibilities

- For **Today** and **Next few days**:
  - Choose a small set of must-do tasks (critical/high only).
  - Choose supporting tasks if capacity allows.
- Respect:
  - Existing calendar events
  - `UserPreferences` (quiet hours, preferred work blocks)
  - Weather annotations (avoid travel in storms, etc.)
- Propose:
  - Study blocks
  - Review sessions before exams
  - Time windows for replying to important emails
- Outputs:
  - `PlanSummary` for UI (Today view)
  - `ActionProposals` for `create_calendar_event` / `create_reminder_event` blocks

---

### AI Build Prompt — Phase 6 (Planner Agent)

“Design the **Planner Agent** for Personal Ops Center.

Inputs:
- Triaged Items for a user (especially critical/high importance).
- Upcoming calendar events (next ~7 days).
- Weather annotations from the Weather Agent.
- UserPreferences (quiet hours, preferred work blocks, meeting preferences).

The Planner Agent should:
- Generate a concise `PlanSummary` for:
  - Today
  - Optional: next 2–3 days
- Select:
  - A small number of must-do items for today (3–5).
  - Additional items for the next few days.
- Propose time blocks:
  - Study blocks before exams.
  - Time to handle email backlog.
  - Any necessary buffers before appointments, considering weather and travel.

Output:
- A structured `PlanSummary` (ready to render in UI).
- A list of `ActionProposals` (create/update calendar events for blocks/reminders) that can be shown in the ‘Pending Actions’ panel.

Implement:
- PlannerAgent with task ranking logic
- Quiet hours and preference handling
- Realistic plan generation (3-5 items max)
- PlanSummary and time block structures
- ActionProposal generation for calendar blocks"

---

## 7. Safety & Scam Agent

**Goal:** Add guardrails so the system doesn’t accidentally help scams or propose dangerous actions.

### Responsibilities

- Email safety:
  - Scan content, sender, links for phishing/scam patterns.
  - Set `ItemAgentMetadata.is_scam` flag and reduce importance.
  - Provide a safety label: `safe`, `suspicious`, `dangerous`.
- Action safety:
  - Inspect `ActionProposals` that:
    - Delete events
    - Modify many events
    - Touch sensitive emails
  - Attach `risk_level` and `warning` message.
  - Optionally auto-reject clearly unsafe actions.

---

### AI Build Prompt — Phase 7 (Safety & Scam Agent)

“Design the **Safety & Scam Agent** for Personal Ops Center.

Responsibilities:

1. Email safety:
   - Given Item data (sender, subject, body):
     - Detect suspicious patterns (phishing, scams, fake login notifications, money transfers).
     - Set:
       - `is_scam` boolean flag.
       - `safety_label` from {safe, suspicious, dangerous}.
     - Provide a short explanation for the label.

2. Action safety:
   - Given a list of `ActionProposals`:
     - Identify potentially dangerous actions (mass deletes, major calendar changes, actions tied to suspicious emails).
     - Attach:
       - `risk_level` from {low, medium, high}.
       - `warning_text`.
     - Optionally mark some actions as auto-rejected when clearly unsafe.

Describe:
- Input/output structures for both email and action safety.
- Heuristics for deciding risk.
- How the Safety Agent should integrate into the Orchestrator:
  - When to run it.
  - How its outputs affect what the UI shows (badges, warnings).
- How to make it conservative, favoring user safety over automation.

Implement SafetyAgent with email scanning and action risk assessment.”

---

## 8. Preference & Feedback Agent

**Goal:** Let the system adapt to you instead of staying dumb and static.

### Responsibilities

- Observe:
  - Which `ActionProposals` you approve vs reject.
  - Which emails you consistently ignore or always act on.
  - How you edit drafts (heavily rewrite or minor tweaks).
- Update:
  - `UserPreferences` and any internal rules (e.g., sender priority weights).
- Provide:
  - Feedback knobs for Triage and Planner Agents (e.g., “bump/nerf this sender or category”).

---

### AI Build Prompt — Phase 8 (Preference & Feedback Agent)

“Design a **Preference & Feedback Agent** for Personal Ops Center.

Inputs:
- `PreferenceSignal` records:
  - When a user approves/rejects/ignores an ActionProposal.
  - When a user heavily edits or barely edits draft emails.
- Item and ActionProposal metadata:
  - Sender domains, categories, importance levels, etc.
- Existing `UserPreferences`.

The agent should:
- Infer simple rules like:
  - ‘Emails from this sender are usually important / usually noise’
  - ‘User rarely wants meetings on Sunday mornings’
  - ‘User prefers short, casual replies to club emails, but formal tone with university offices’
- Update:
  - `UserPreferences` (structured fields).
  - Possibly a simple per-sender or per-domain weighting table to influence Triage and Planner.

Describe:
- How often the agent should run (e.g., daily, after N new signals).
- What kind of rules it should infer.
- How it should express these rules so other agents can consume them easily (structured config, not free-text).
- How to avoid overfitting (e.g., not changing preferences after one data point).

Implement PreferenceAgent with signal processing and preference updates.”

---

## 9. Frontend UX: Layout, Navigation, States

**Goal:** Define UX for a **robust** webapp: pages, panels, states — without touching styling implementation.

### Main Views

- **Inbox**
  - Left: combined email list (Gmail + Outlook) with filters.
  - Right: email detail (summary, full content, agent insights, actions).
- **Today**
  - Daily timeline + list of must-do tasks.
- **Planner**
  - Multi-day view with proposed blocks.
- **Agent Console**
  - Timeline/log of agent runs and status.
- **Settings**
  - Provider connections, preferences, safety toggles.

### Cross-cutting UI Elements

- Top nav or sidebar for view switching.
- “Pending Actions” panel (slide-out or fixed).
- Chat/command box (“Ask your agent…”) in Today/Planner.

---

### AI Build Prompt — Phase 9 (UX Structure)

“Help me design the **frontend UX structure** for Personal Ops Center.

I want a modern, minimal SPA with:

- Views:
  - Inbox
  - Today
  - Planner
  - Agent Console
  - Settings
- Cross-cutting elements:
  - A ‘Pending Actions’ panel showing proposed actions and approve/edit/reject controls.
  - A small chat/command bar to talk to the orchestrator (e.g., ‘plan my day’, ‘handle important emails from today’).
  - Soft animations and state transitions, but minimal chrome and no heavy borders.

Describe:
- The layout and components for each view.
- How the user moves between views.
- How the ‘Pending Actions’ panel integrates into each view.
- How the Agent Console should present agent logs in a way that makes the multi-agent workflow understandable.
- Different UI states:
  - First-time user (no accounts connected)
  - Connected but no data yet
  - Normal daily use
  - Error states (e.g., integration problem, agent failures)

I don’t need any code or CSS, just a detailed UX spec I can turn into components.”

---

## 10. Frontend: Inbox & Pending Actions Experience

**Goal:** Nail the experience of handling email + proposed actions.

### Inbox Experience

- Email list:
  - Source icon (Gmail/Outlook)
  - Subject, sender, timestamp
  - Importance badge, category chip
- Email detail:
  - Summary block (TL;DR, bullet points)
  - Full content (expandable)
  - Agent insights:
    - Category, due date, safety label
  - Available actions:
    - Draft reply
    - Add to calendar
    - Mark ignore

### Pending Actions Panel

- Each `ActionProposal` as a card:
  - What will happen in plain language
  - Agent that proposed it
  - Risk badge + explanation
  - Buttons: Approve, Edit, Reject

---

### AI Build Prompt — Phase 10 (Inbox & Actions UX)

“Design the **Inbox view** and **Pending Actions panel** for Personal Ops Center.

Inbox:
- Combined email list from Gmail + Outlook on the left.
- Email detail on the right:
  - Show summary (TL;DR, bullets).
  - Show metadata: category, importance, due date, safety label, source account icon.
  - Show buttons for:
    - ‘Draft reply’ (invokes Email Agent)
    - ‘Add to calendar’ (invokes Event Agent)
    - ‘Mark as low priority’ or ‘Ignore’

Pending Actions:
- A panel showing current `ActionProposals`:
  - Each card should include:
    - A human-readable description of the action.
    - Which agent proposed it.
    - Risk and safety info from Safety Agent.
    - Explanation text from Explanation Agent.
  - Buttons:
    - Approve (triggers executor)
    - Edit (opens simple inline editor for email text or event times)
    - Reject (records PreferenceSignal)

Describe:
- UI states for loading, empty, and error.
- How to keep the UI responsive and simple even when there are many items.
- How to visually show which emails already have actions proposed for them.

No code, just UX behavior and layout details.”

---

## 11. Frontend: Today, Planner & Agent Console

**Goal:** Make planning and transparency feel natural.

### Today View

- Timeline of today’s events + proposed blocks.
- List of “Today’s Must-Do” tasks from Planner Agent.
- Integration with Pending Actions (approve new blocks directly from here).

### Planner View

- Multi-day view (3–7 days).
- Display:
  - Fixed events
  - Proposed blocks
  - Weather hints (e.g., icon next to time slots).
- Controls:
  - “Re-run planner” button
  - Filters (e.g., show only exams, only study blocks)

### Agent Console

- Timeline or list of recent runs:
  - Orchestrator intents: refresh_inbox, plan_day, handle_item
  - Agents involved and their status
  - Errors surfaced clearly
- Optional detail panel showing:
  - How many items each agent processed
  - Summary of what changed (e.g., “5 items triaged, 3 action proposals created”)

---

### AI Build Prompt — Phase 11 (Today, Planner, Agent Console UX)

“Design the **Today**, **Planner**, and **Agent Console** views for Personal Ops Center.

Today:
- Show a timeline of today’s schedule (calendar events + proposed blocks).
- Show a list of ‘Today’s Must-Do’ tasks from the Planner Agent.
- Integrate Pending Actions where relevant (e.g., suggested study blocks).

Planner:
- Show a 3–7 day view of events and proposed blocks.
- Indicate weather context where it matters (icons, hints).
- Allow the user to:
  - Re-run the Planner Agent.
  - Toggle which types of blocks they want to see (study, email, commitments).

Agent Console:
- Act as a transparent window into the multi-agent system.
- For each orchestrator run, show:
  - Intent (refresh_inbox, plan_day, handle_item)
  - Which agents ran
  - How many items they acted on
  - Any errors, surfaced clearly.
- Allow the user to expand a log entry to see a short summary of changes (e.g., ‘Triage Agent updated 10 items; Planner created 4 new action proposals’).

Describe:
- Layout and components for these views.
- How transitions between them should feel (smooth but subtle).
- How the Agent Console can make the multi-agent behavior understandable to a non-developer user.

No code, just UX spec.”

---

## 12. Execution & Error Handling

**Goal:** Solidify the executor so the system feels trustworthy and failures are controlled.

### Executor Responsibilities

- Take an `ActionProposal` with status `approved`.
- Perform provider-specific action:
  - Create Gmail draft
  - Create Outlook draft
  - Create/update/delete Calendar event
- Log result in `ExecutionLog`.
- Update `ActionProposal.status` to `executed` or `failed`.

### Error Handling Expectations

- If an action fails:
  - Mark `failed` with error message.
  - Do not crash the system.
  - Surface failure in UI (e.g., warning on that card).
- Orchestrator should:
  - Never retry blindly.
  - Let user decide what to do with failed actions.

---

### AI Build Prompt — Phase 12 (Executor & Errors)

“Design the **Action Executor** and error-handling behavior for Personal Ops Center.

Executor:
- Takes an `ActionProposal` with status = pending/approved.
- For each `action_type` (create_email_draft, create_calendar_event, update_calendar_event, etc.):
  - Calls the appropriate provider API (Gmail, Outlook, Google Calendar).
  - Handles provider responses and errors.
  - Writes `ExecutionLog` entries.
  - Updates `ActionProposal.status` to `executed` on success, or `failed` on error.

Error handling:
- Define how to handle provider errors (rate limit, auth failure, invalid data).
- Define what the UI should show when an action fails (e.g., warning badge with tooltip).
- Define how the system avoids performing actions twice.

Describe:
- The execution flow in steps.
- The status transitions of ActionProposal.
- Logging expectations for debugging.

Implement Action Executor with provider API calls and error handling.”

---

## 13. Final Integration & End-to-End Flows

**Goal:** Make sure all pieces play together: inbox refresh, email handling, planning, execution.

### End-to-End Flows to Validate

1. **Inbox Refresh**
   - User hits Refresh
   - Ingestion pulls new emails/events + updates Items
   - Triage Agent runs, updates metadata
   - Specialist agents generate summaries and proposals
   - Safety Agent annotates risk
   - UI updates Inbox + Pending Actions + Today

2. **Handle Single Email**
   - User clicks email
   - Summary + metadata show
   - User clicks “Draft reply”
   - Email Agent generates ActionProposal
   - Safety Agent checks if needed
   - User approves → Executor creates draft
   - UI marks email as “draft ready”

3. **Plan Day**
   - User asks “plan my day”
   - Orchestrator gathers context, calls Planner Agent
   - Planner outputs PlanSummary + ActionProposals
   - Safety Agent scans proposals
   - UI shows timeline + actions
   - User approves study blocks and reminders → Executor creates events

---

### AI Build Prompt — Phase 13 (End-to-End Integration Checklist)

“Help me produce an **end-to-end integration checklist** for Personal Ops Center.

I want to verify and polish these flows:

1. Inbox Refresh:
   - Ingestion → Triage → specialist agents → Safety → UI updates.

2. Handle Single Email:
   - User opens email → sees summary and metadata → requests draft reply → Email Agent proposes `ActionProposal` → Safety Agent checks → user approves → executor creates draft in Gmail/Outlook.

3. Plan Day:
   - User requests day planning → Orchestrator collects Items, events, weather, preferences → Planner Agent proposes PlanSummary and calendar ActionProposals → Safety Agent checks → user approves → executor creates blocks.

For each flow, list:
- Preconditions in the database.
- Which services and agents are involved.
- What should be written to which tables.
- What the user should see in the UI at each step.
- Edge cases and failure modes I should test.



---
