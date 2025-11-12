# Personal Ops Center - System Architecture

**Version:** 1.0  
**Date:** November 12, 2025  
**Status:** Phase 0 - Architecture Design

## Executive Summary

The Personal Ops Center is a multi-agent AI system that monitors email accounts (Gmail, Outlook), calendar events, and weather to provide intelligent assistance for personal operations. The system proposes actions but **never executes them without explicit user approval**.

## Core Principle

**Agents propose, users approve, executors act.**

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐     ┌──────────────┐
│   Data      │────▶│  AI Agents   │────▶│   Action    │────▶│   Executor   │
│  Sources    │     │ (Read-Only)  │     │  Proposals  │     │ (Write-Only) │
└─────────────┘     └──────────────┘     └─────────────┘     └──────────────┘
                                                  │
                                                  ▼
                                          ┌──────────────┐
                                          │     User     │
                                          │   Approval   │
                                          └──────────────┘
```

## System Architecture Overview

### Three-Layer Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         FRONTEND LAYER                               │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ │
│  │  Inbox   │ │  Today   │ │ Planner  │ │  Agent   │ │ Settings │ │
│  │   View   │ │   View   │ │   View   │ │ Console  │ │   View   │ │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘ │
│                                                                       │
│  ┌──────────────────────────────────────────────────────────┐       │
│  │         Pending Actions Panel (Approve/Edit/Reject)      │       │
│  └──────────────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼ HTTP/WebSocket
┌─────────────────────────────────────────────────────────────────────┐
│                          BACKEND API LAYER                           │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │                    FastAPI REST API                         │    │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │    │
│  │  │  Auth &  │ │  OAuth   │ │  Items   │ │ Actions  │      │    │
│  │  │  Users   │ │ Connect  │ │   API    │ │   API    │      │    │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘      │    │
│  └────────────────────────────────────────────────────────────┘    │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │                   Ingestion Services                        │    │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │    │
│  │  │  Gmail   │ │ Outlook  │ │ Calendar │ │ Weather  │      │    │
│  │  │  Sync    │ │   Sync   │ │   Sync   │ │  Fetch   │      │    │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘      │    │
│  └────────────────────────────────────────────────────────────┘    │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │                    Action Executor                          │    │
│  │  (Only component that writes to external services)         │    │
│  └────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼ Internal API Calls
┌─────────────────────────────────────────────────────────────────────┐
│                    AI ORCHESTRATION LAYER                            │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │                      Orchestrator                           │    │
│  │  - Receives intents (refresh_inbox, plan_day, etc.)        │    │
│  │  - Routes to appropriate agents                            │    │
│  │  - Manages agent state and context                         │    │
│  │  - Writes AgentRunLog entries                              │    │
│  └────────────────────────────────────────────────────────────┘    │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │                     Agent Registry                          │    │
│  │  Maps agent names to implementations                       │    │
│  └────────────────────────────────────────────────────────────┘    │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────────┤
│  │                    Specialist Agents                            ││
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐          ││
│  │  │  Triage  │ │  Email   │ │  Event   │ │ Weather  │          ││
│  │  │  Agent   │ │  Agent   │ │  Agent   │ │  Agent   │          ││
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘          ││
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐                       ││
│  │  │ Planner  │ │  Safety  │ │Preference│                       ││
│  │  │  Agent   │ │  Agent   │ │  Agent   │                       ││
│  │  └──────────┘ └──────────┘ └──────────┘                       ││
│  └─────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      DATA PERSISTENCE LAYER                          │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │                    PostgreSQL Database                      │    │
│  │  - Users, ConnectedAccounts                                │    │
│  │  - Items, ItemAgentMetadata                                │    │
│  │  - ActionProposals, ExecutionLogs                          │    │
│  │  - UserPreferences, PreferenceSignals                      │    │
│  │  - AgentRunLogs                                            │    │
│  └────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
```

## Service Responsibilities

### 1. Frontend Layer (React SPA)

**Technology:** React 18+, TypeScript, TailwindCSS  
**Communication:** REST API + WebSocket/SSE for streaming

**Views:**
- **Inbox View**: Combined email list with filtering, detail view with agent insights
- **Today View**: Timeline of today's schedule + must-do tasks
- **Planner View**: Multi-day calendar with proposed blocks
- **Agent Console**: Transparent window into agent activity
- **Settings**: OAuth connections, preferences, feature toggles

**Cross-Cutting Components:**
- **Pending Actions Panel**: Slide-out or fixed panel showing all action proposals
- **Action Cards**: Display proposal details with Approve/Edit/Reject buttons
- **Streaming Updates**: Real-time agent outputs via WebSocket

**Responsibilities:**
- Render all user interfaces
- Handle user input and interactions
- Display action proposals for approval
- Stream agent reasoning and outputs
- Manage client-side state (React Context/Redux)
- No direct business logic or AI calls

### 2. Backend API Layer (FastAPI)

**Technology:** FastAPI, Python 3.10+, SQLAlchemy, Pydantic  
**Communication:** REST endpoints, internal RPC to orchestrator

**Services:**

#### 2a. Authentication & User Management
```python
POST   /api/auth/register
POST   /api/auth/login
GET    /api/auth/me
PUT    /api/users/{user_id}/preferences
```

**Responsibilities:**
- User registration and authentication
- JWT token management
- User preferences CRUD
- Session management

#### 2b. OAuth Integration Service
```python
GET    /api/accounts
POST   /api/accounts/connect/{provider}  # gmail, outlook, calendar
GET    /api/accounts/{account_id}/status
DELETE /api/accounts/{account_id}
```

**Responsibilities:**
- OAuth flow initiation and callback handling
- Token storage and refresh
- Provider health checks
- Account disconnection

#### 2c. Ingestion Services

**Gmail Sync:**
- Fetch last N emails via Gmail API
- Normalize to `Item` schema
- Store in database
- Trigger orchestrator refresh

**Outlook Sync:**
- Fetch emails via Microsoft Graph API
- Same normalization and storage
- Handle pagination and delta queries

**Calendar Sync:**
- Fetch upcoming events (next 7-14 days)
- Normalize and store
- Handle recurring events

**Weather Fetch:**
- Poll weather API for user's location
- Store forecast data
- Make available to agents

**API Endpoints:**
```python
POST   /api/sync/refresh-inbox
POST   /api/sync/refresh-calendar
GET    /api/sync/status
```

#### 2d. Items API
```python
GET    /api/items
GET    /api/items/{item_id}
PUT    /api/items/{item_id}/metadata
POST   /api/items/{item_id}/archive
```

**Responsibilities:**
- Read access to ingested items
- Item metadata updates
- Filtering and pagination
- No external API calls

#### 2e. Actions API
```python
GET    /api/action-proposals
GET    /api/action-proposals/{proposal_id}
POST   /api/action-proposals/{proposal_id}/approve
POST   /api/action-proposals/{proposal_id}/reject
PUT    /api/action-proposals/{proposal_id}/edit
```

**Responsibilities:**
- List and filter action proposals
- Handle user approval/rejection/edits
- Trigger executor when approved
- Record preference signals

#### 2f. Orchestrator API
```python
POST   /api/orchestrator/execute
GET    /api/orchestrator/runs
GET    /api/orchestrator/runs/{run_id}
```

**Responsibilities:**
- Trigger orchestrator intents
- Return agent run status
- Stream agent outputs (SSE/WebSocket)

#### 2g. Action Executor

**Critical Constraint:** This is the ONLY component that writes to external services.

**Responsibilities:**
- Execute approved ActionProposals
- Call Gmail/Outlook/Calendar APIs
- Create drafts, events, updates
- Log all executions
- Handle provider errors gracefully
- Update ActionProposal status

**Supported Actions:**
- `create_email_draft` (Gmail or Outlook)
- `create_calendar_event` (Google Calendar)
- `update_calendar_event`
- `delete_calendar_event`
- `create_reminder_event`

**Error Handling:**
- Rate limit retries with backoff
- Token refresh on 401
- Mark failed actions with error details
- Never crash on single failure

### 3. AI Orchestration Layer

**Technology:** LangGraph, LangChain, NVIDIA NIM APIs  
**Communication:** Called by Backend API, reads/writes database

#### 3a. Orchestrator

**Responsibilities:**
- Receive high-level intents from Backend API
- Determine which agents to run and in what order
- Build context for each agent (user_id, relevant items, preferences)
- Execute agents via LangGraph workflow
- Collect agent outputs
- Write ActionProposals to database
- Write AgentRunLog entries
- Return summary to API

**Intents:**
- `refresh_inbox`: Triage new items, generate summaries, detect scams
- `plan_day`: Generate daily plan with time blocks
- `handle_item(item_id)`: Process specific email/event
- `draft_reply(item_id)`: Generate email draft
- `schedule_event(item_id)`: Extract and propose calendar event

**State Management:**
```python
class OpsAgentState(BaseModel):
    user_id: str
    intent: str
    items: List[Dict]
    action_proposals: List[Dict]
    agent_logs: List[Dict]
    user_preferences: Dict
    weather_context: Dict
    errors: List[Dict]
```

**Workflow Example (refresh_inbox):**
```
1. Fetch new Items from database
2. Run TriageAgent → updates ItemAgentMetadata
3. Run SafetyAgent → marks scams, sets risk levels
4. Run EmailAgent (for high-priority items) → generates summaries
5. Run EventAgent (for meeting/invite items) → proposes calendar events
6. Write all ActionProposals to database
7. Write AgentRunLog
8. Return summary
```

#### 3b. Agent Registry

Simple mapping of agent names to implementations:

```python
AGENT_REGISTRY = {
    "triage": TriageAgent,
    "email": EmailAgent,
    "event": EventAgent,
    "weather": WeatherAgent,
    "planner": PlannerAgent,
    "safety": SafetyAgent,
    "preference": PreferenceAgent,
}
```

**Responsibilities:**
- Lookup agents by name
- Validate agent interface
- Enable/disable agents via config

#### 3c. Agent Interface

All agents implement:

```python
class BaseAgent(ABC):
    @abstractmethod
    async def run(self, context: AgentContext) -> AgentResult:
        """
        Execute agent logic.
        
        Args:
            context: Contains user_id, items, preferences, etc.
            
        Returns:
            AgentResult with outputs and any action proposals
        """
        pass
```

**Constraints:**
- Agents are READ-ONLY (no external API writes)
- Agents write to database (Items metadata, ActionProposals)
- Agents use LLM APIs (NVIDIA NIM) for intelligence
- Agents return structured JSON outputs

#### 3d. Specialist Agents

**Triage Agent:**
- Input: List of Item IDs
- Process: Classify category, importance, action_type; extract due dates
- Output: Writes ItemAgentMetadata

**Email Agent:**
- Input: Item IDs for emails
- Process: Generate TL;DR, bullets, draft replies
- Output: Summaries in metadata, ActionProposals for drafts

**Event Agent:**
- Input: Item IDs for meetings/invites
- Process: Extract event details, propose calendar actions
- Output: ActionProposals (create_calendar_event, etc.)

**Weather Agent:**
- Input: Weather forecast + upcoming events
- Process: Tag time slots with weather context
- Output: Weather annotations for Planner

**Planner Agent:**
- Input: Triaged items, calendar, weather, preferences
- Process: Select must-do tasks, propose time blocks
- Output: PlanSummary + ActionProposals for blocks

**Safety Agent:**
- Input: Items + ActionProposals
- Process: Detect scams, assess action risk
- Output: Sets is_scam flag, risk_level on proposals

**Preference Agent:**
- Input: PreferenceSignals (approved/rejected actions, edited drafts)
- Process: Infer patterns, update preferences
- Output: Updated UserPreferences

### 4. Data Persistence Layer

**Technology:** PostgreSQL 15+, SQLAlchemy ORM, Alembic migrations

**Tables:** (Detailed schema in Phase 1)
- `users`
- `connected_accounts`
- `items`
- `item_agent_metadata`
- `action_proposals`
- `execution_logs`
- `user_preferences`
- `preference_signals`
- `agent_run_logs`

## Communication Patterns

### 1. User Initiates Refresh

```
User clicks "Refresh" in UI
  ↓
Frontend → POST /api/sync/refresh-inbox
  ↓
Backend Ingestion Service:
  - Calls Gmail API
  - Calls Outlook API
  - Normalizes to Items
  - Saves to database
  ↓
Backend → POST /api/orchestrator/execute (intent: refresh_inbox)
  ↓
Orchestrator:
  - Runs Triage, Safety, Email, Event agents
  - Writes ActionProposals
  ↓
Backend returns status to Frontend
  ↓
Frontend polls or streams updates
  ↓
User sees new items + action proposals
```

### 2. User Approves Action

```
User clicks "Approve" on ActionProposal
  ↓
Frontend → POST /api/action-proposals/{id}/approve
  ↓
Backend API:
  - Updates ActionProposal.status = 'approved'
  - Writes PreferenceSignal (approved)
  ↓
Backend calls Action Executor
  ↓
Executor:
  - Reads ActionProposal payload
  - Calls Gmail/Outlook/Calendar API
  - Creates draft or event
  - Writes ExecutionLog
  - Updates ActionProposal.status = 'executed' or 'failed'
  ↓
Backend returns result to Frontend
  ↓
Frontend updates UI
```

### 3. Agent Streaming Output

```
User requests "Plan my day"
  ↓
Frontend → POST /api/orchestrator/execute (intent: plan_day)
  ↓
Backend opens WebSocket/SSE connection
  ↓
Orchestrator runs Planner Agent
  ↓
Agent reasoning streamed back:
  - "Analyzing 15 high-priority items..."
  - "Checking calendar conflicts..."
  - "Proposing 3 study blocks..."
  ↓
Frontend displays in real-time
```

## Technology Stack Summary

| Layer | Technologies |
|-------|-------------|
| Frontend | React 18+, TypeScript, TailwindCSS, React Query, WebSocket |
| Backend API | FastAPI, Pydantic, SQLAlchemy, Python 3.10+ |
| Orchestrator | LangGraph, LangChain, NVIDIA NIM APIs |
| Database | PostgreSQL 15+, Alembic |
| OAuth | google-auth, msal (Microsoft) |
| Weather | OpenWeatherMap API |
| Deployment | Docker, Docker Compose |
| CI/CD | GitHub Actions |
| Monitoring | OpenTelemetry (optional) |

## Security & Privacy

### OAuth Token Storage
- Encrypted at rest in database
- Scoped permissions (read emails, create drafts)
- Refresh token rotation
- Revocation support

### API Security
- JWT authentication for all endpoints
- HTTPS only in production
- CORS properly configured
- Rate limiting per user

### Data Privacy
- User data isolated by user_id
- No shared data between users
- Email content stored encrypted (optional)
- Compliance: User can delete all data

### Agent Safety
- Safety Agent scans all emails for scams
- Risk levels on all action proposals
- High-risk actions require explicit confirmation
- Option to auto-reject dangerous actions

## Deployment Architecture

### Development
```
docker-compose.yaml:
  - postgres
  - backend-api
  - orchestrator (separate or same container)
  - frontend (dev server)
```

### Production (Future)
```
- Frontend: Static hosting (Vercel, Netlify)
- Backend API: Container platform (Cloud Run, Fargate)
- Orchestrator: Container or serverless functions
- Database: Managed PostgreSQL (RDS, Cloud SQL)
- OAuth: Managed secrets (Secret Manager)
```

## Failure Modes & Error Handling

### External API Failures

**Gmail/Outlook/Calendar down:**
- Ingestion fails gracefully
- Shows last synced time
- Retries with exponential backoff
- User notified of sync issues

**NVIDIA NIM API down:**
- Orchestrator queues intents
- Returns cached/fallback responses
- User notified AI unavailable

### Agent Failures

**Single agent fails:**
- Orchestrator continues with other agents
- Logs error to AgentRunLog
- Returns partial results
- UI shows which agent failed

**Orchestrator crashes:**
- No data loss (state in database)
- Can resume or retry
- User manually triggers refresh

### Executor Failures

**Action execution fails:**
- ActionProposal marked as 'failed'
- Error logged in ExecutionLog
- User can retry or edit
- No retries without user approval

## Next Steps

After Phase 0 approval:
1. **Phase 1**: Design detailed database schema
2. **Phase 2**: Implement OAuth and ingestion services
3. **Phase 3**: Build orchestrator skeleton

---

**Architecture Status:** ✅ Phase 0 Complete - Ready for Phase 1

