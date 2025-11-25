# Personal Ops Center

<div align="center">

**An intelligent multi-agent AI system for personal productivity automation**

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-blue.svg)](https://reactjs.org/)
[![LangChain](https://img.shields.io/badge/LangChain-0.1-yellow.svg)](https://www.langchain.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.0.20-orange.svg)](https://github.com/langchain-ai/langgraph)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

[Features](#features) • [Quick Start](#quick-start) • [Architecture](#architecture) • [Documentation](#documentation) • [Contributing](#contributing)

</div>

---

## Overview

Personal Ops Center is a production-ready multi-agent AI system that automates email triage, calendar management, and daily planning. Built with **LangChain** and **LangGraph** for intelligent agent orchestration, it learns from your preferences and helps you stay organized.

### Key Capabilities

- **Intelligent Email Triage**: Automatically classifies, prioritizes, and summarizes emails
- **Calendar Automation**: Extracts events, proposes meetings, and manages your schedule
- **Daily Planning**: AI-powered daily plans with time blocks and focus areas
- **Safety & Security**: Built-in scam detection and risk assessment
- **Preference Learning**: Adapts to your work style over time
- **Multi-Provider Support**: Works with Gmail, Outlook, and Google Calendar

---

## Features

### Multi-Agent System

```mermaid
mindmap
  root((Personal Ops Center))
    Triage Agent
      Classification
      Prioritization
      Deadline Extraction
      Action Suggestions
    Email Agent
      Summarization
      Draft Generation
      Tone Adaptation
      Key Points Extraction
    Event Agent
      Calendar Extraction
      Event Proposals
      Deadline Detection
      Meeting Scheduling
    Planner Agent
      Daily Plans
      Time Blocks
      Focus Areas
      Context Awareness
    Safety Agent
      Phishing Detection
      Scam Prevention
      Risk Assessment
      Content Flagging
    Preference Agent
      Feedback Learning
      Preference Updates
      Pattern Recognition
      Auto-Tuning
```

### Technology Stack

```mermaid
graph TD
    subgraph Frontend_Stack["Frontend Stack"]
        React[React 18]
        TS[TypeScript]
        Vite[Vite]
        UI[Modern UI]
        React --> TS
        TS --> Vite
        Vite --> UI
    end
    
    subgraph Backend_Stack["Backend Stack"]
        FastAPI[FastAPI]
        SQLAlchemy[SQLAlchemy ORM]
        Alembic[Alembic Migrations]
        REST[RESTful API]
        FastAPI --> SQLAlchemy
        SQLAlchemy --> Alembic
        FastAPI --> REST
    end
    
    subgraph AI_Stack["AI & Orchestration Stack"]
        LangChain[LangChain]
        LangGraph[LangGraph]
        OpenAI_Stack[OpenAI API]
        NVIDIA_Stack[NVIDIA NIM]
        State[State Management]
        LangChain --> LangGraph
        LangGraph --> State
        LangChain --> OpenAI_Stack
        LangChain --> NVIDIA_Stack
    end
    
    subgraph Database_Stack["Database Stack"]
        PostgreSQL[(PostgreSQL)]
        JSONB[JSONB Metadata]
        Indexes[Optimized Indexes]
        FTS[Full-Text Search]
        PostgreSQL --> JSONB
        PostgreSQL --> Indexes
        PostgreSQL --> FTS
    end
    
    Frontend_Stack --> Backend_Stack
    Backend_Stack --> AI_Stack
    Backend_Stack --> Database_Stack
    AI_Stack --> Database_Stack
```

---

## Quick Start

### Prerequisites

- **Docker & Docker Compose** (for containerized setup)
- **Python 3.10+** (for local development)
- **Node.js 18+** (for frontend development)
- **PostgreSQL 14+** (or use Docker)

### AI Provider Setup

Choose one:

1. **OpenAI** (Recommended for development)
   ```bash
   OPENAI_API_KEY=your-key-here
   AI_PROVIDER=openai
   OPENAI_MODEL=gpt-4o-mini
   ```

2. **NVIDIA NIM** (Production-ready)
   ```bash
   NVIDIA_API_KEY=your-key-here
   AI_PROVIDER=nvidia
   ```

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Sant0-9/Mini-os.git
   cd multiagents
   ```

2. **Configure environment**
   ```bash
   cp env.example .env
   # Edit .env and add your API keys
   ```

3. **Start with Docker Compose**
   ```bash
   docker-compose up -d
   ```

4. **Run database migrations**
   ```bash
   docker-compose exec backend-api alembic upgrade head
   ```

5. **Access the application**
   - Frontend: http://localhost:3001
   - API Docs: http://localhost:8001/docs
   - Health Check: http://localhost:8001/health

### Alternative: Local Development

**Backend**
```bash
# Install dependencies
pip install -r requirements.txt

# Set up PostgreSQL (or use Docker)
# Update alembic.ini with your database URL

# Run migrations
alembic upgrade head

# Start server
uvicorn backend.api.server:app --reload --port 8001
```

**Frontend**
```bash
cd frontend
npm install
npm run dev  # Runs on http://localhost:3001
```

---

## Architecture

### System Overview

```mermaid
graph TB
    subgraph Frontend["Frontend Layer (React + TypeScript)"]
        Today[Today View]
        Inbox[Inbox View]
        Planner[Planner View]
        Chat[Chat Assistant]
        Actions[Actions View]
    end

    subgraph Backend["Backend API (FastAPI)"]
        API[FastAPI Server]
        Routes[API Routes]
        DB_Session[Database Session]
    end

    subgraph Orchestrator["Orchestrator (LangGraph)"]
        LG[LangGraph StateGraph]
        Triage[Triage Agent]
        Safety[Safety Agent]
        Email[Email Agent]
        Event[Event Agent]
        Planner_Agent[Planner Agent]
        Preference[Preference Agent]
    end

    subgraph LLM["LLM Client (LangChain)"]
        LC[LangChain Client]
        OpenAI[OpenAI API]
        NVIDIA[NVIDIA NIM]
    end

    subgraph Database["Database (PostgreSQL)"]
        PG[(PostgreSQL)]
        Tables[Tables: items, actions, logs, etc.]
    end

    subgraph Integrations["External Integrations"]
        Gmail[Gmail OAuth]
        Outlook[Outlook OAuth]
        Calendar[Google Calendar]
        Weather[Weather API]
    end

    Frontend -->|HTTP/REST| Backend
    Backend -->|Calls| Orchestrator
    Orchestrator -->|Uses| LLM
    Backend -->|Reads/Writes| Database
    Backend -->|Fetches Data| Integrations
    Orchestrator -->|Stores Results| Database
    LLM -->|API Calls| OpenAI
    LLM -->|API Calls| NVIDIA
```

### Agent Workflow (LangGraph)

The orchestrator uses **LangGraph StateGraph** to manage multi-agent execution:

```mermaid
stateDiagram-v2
    [*] --> Triage: refresh_inbox intent
    
    Triage --> Safety: Classify items
    Safety --> Email: Check for scams
    Email --> Event: Generate summaries
    Event --> [*]: Extract events
    
    [*] --> Planner: plan_day intent
    Planner --> [*]: Generate plan
    
    [*] --> Preference: learn_preferences intent
    Preference --> [*]: Update preferences
    
    note right of Triage
        Classifies emails/events
        Assigns importance
        Extracts deadlines
    end note
    
    note right of Safety
        Detects phishing/scams
        Assesses action risks
        Flags suspicious content
    end note
    
    note right of Email
        Summarizes emails
        Generates draft replies
        Respects tone preferences
    end note
    
    note right of Event
        Extracts calendar events
        Proposes calendar entries
        Detects deadlines
    end note
```

### Data Flow

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant Backend
    participant Orchestrator
    participant Agents
    participant LLM
    participant Database
    participant Integrations

    User->>Frontend: Interact with UI
    Frontend->>Backend: API Request
    Backend->>Orchestrator: Execute Intent
    
    Orchestrator->>Agents: Route to Agent
    Agents->>LLM: Generate Response
    LLM-->>Agents: LLM Output
    Agents->>Orchestrator: Agent Result
    Orchestrator->>Database: Store Proposals
    
    Backend->>Database: Query Data
    Database-->>Backend: Return Results
    Backend-->>Frontend: API Response
    Frontend-->>User: Display Data
    
    Note over Integrations,Database: Background Sync
    Integrations->>Backend: Fetch Emails/Events
    Backend->>Database: Store Items
    Database->>Orchestrator: Trigger Processing
```

### Technology Evolution

```mermaid
graph LR
    subgraph Foundation["Foundation (2018-2020)"]
        BERT[BERT]
        GPT2[GPT-2]
        T5[T5]
    end
    
    subgraph Modern["Modern LLMs (2021-2022)"]
        GPT3[GPT-3]
        PaLM[PaLM]
        LLaMA[LLaMA]
    end
    
    subgraph Current["Current (2023-2024)"]
        GPT4[GPT-4]
        Claude[Claude]
        Llama3[Llama 3]
    end
    
    subgraph OurStack["Our Stack"]
        LangChain[LangChain]
        LangGraph[LangGraph]
        OpenAI_Int[OpenAI Integration]
        NVIDIA_Int[NVIDIA NIM]
    end
    
    Foundation --> Modern
    Modern --> Current
    Current --> OurStack
    
    style OurStack fill:#4CAF50,stroke:#2E7D32,stroke-width:3px
    style Current fill:#2196F3,stroke:#1565C0,stroke-width:2px
```

---

## API Documentation

### Core Endpoints

**Inbox Management**
- `GET /api/inbox` - List inbox items (supports filtering)
- `GET /api/inbox/{item_id}` - Get specific item details

**Planner**
- `GET /api/planner/today` - Generate today's plan
- `POST /api/planner/regenerate` - Regenerate plan with new context

**Actions**
- `GET /api/actions/pending` - List pending action proposals
- `POST /api/actions/{id}/approve` - Approve and execute action
- `POST /api/actions/{id}/reject` - Reject action proposal

**Sync & Integration**
- `POST /api/sync/trigger` - Manually trigger data sync
- `GET /api/sync/status` - Get sync status for all accounts

**Chat Assistant**
- `POST /api/chat/message` - Send message to AI assistant
- `GET /api/chat/history/{session_id}` - Get chat history

### Interactive API Docs

Full interactive documentation available at:
- Swagger UI: http://localhost:8001/docs
- ReDoc: http://localhost:8001/redoc

---

## Development

### Project Structure

```mermaid
graph TD
    Root[multiagents/]
    
    Root --> Backend[backend/]
    Root --> Orchestrator[orchestrator/]
    Root --> Frontend[frontend/]
    Root --> Tests[tests/]
    Root --> Alembic[alembic/]
    Root --> Docs[docs/]
    
    Backend --> API[api/]
    Backend --> Integrations[integrations/]
    Backend --> Ingestion[ingestion/]
    Backend --> Executor[executor/]
    
    API --> Models[models/]
    API --> Routes[routes/]
    API --> Server[server.py]
    
    Orchestrator --> Agents[agents/]
    Orchestrator --> State[state.py]
    Orchestrator --> Orchestrator_Py[orchestrator.py]
    
    Agents --> Triage_File[triage_agent.py]
    Agents --> Email_File[email_agent.py]
    Agents --> Event_File[event_agent.py]
    Agents --> Planner_File[planner_agent.py]
    Agents --> Safety_File[safety_agent.py]
    Agents --> Preference_File[preference_agent.py]
    
    Frontend --> Src[src/]
    Src --> Components[components/]
    Src --> Pages[pages/]
    Src --> API_Client[api/]
    
    style Root fill:#2196F3,stroke:#1565C0,stroke-width:3px
    style Orchestrator fill:#4CAF50,stroke:#2E7D32,stroke-width:2px
    style Agents fill:#FF9800,stroke:#F57C00,stroke-width:2px
```

### Code Quality

**Pre-commit Hooks**
- Python syntax validation
- Black formatting (line length 119)
- Flake8 linting
- Emoji detection in code
- Commit message validation

**CI/CD Pipeline**
- Automated testing on push/PR
- Docker image builds
- Security scanning with Trivy
- Coverage reports

**Running Checks Locally**
```bash
# Format code
black --line-length=119 .

# Lint
flake8 . --max-line-length=119 --extend-ignore=E203,W503

# Type check
mypy . --ignore-missing-imports

# Run tests
pytest --cov=. --cov-report=html
```

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_orchestrator.py

# Run with verbose output
pytest -v
```

---

## Database Schema

### Entity Relationship Diagram

```mermaid
erDiagram
    users ||--o{ connected_accounts : "has"
    users ||--o{ items : "owns"
    users ||--o{ action_proposals : "creates"
    users ||--|| user_preferences : "has"
    users ||--o{ preference_signals : "generates"
    users ||--o{ agent_run_logs : "triggers"
    users ||--o{ chat_sessions : "has"
    
    connected_accounts ||--o{ items : "sources"
    
    items ||--o| item_agent_metadata : "has"
    items ||--o{ action_proposals : "triggers"
    
    action_proposals ||--o{ execution_logs : "executes"
    
    chat_sessions ||--o{ chat_messages : "contains"
    
    users {
        uuid id PK
        string email UK
        string password_hash
        string timezone
        datetime created_at
    }
    
    connected_accounts {
        uuid id PK
        uuid user_id FK
        string provider
        text access_token
        text refresh_token
        datetime token_expires_at
    }
    
    items {
        uuid id PK
        uuid user_id FK
        uuid source_account_id FK
        string source_type
        string title
        text body_preview
        text body_full
        datetime created_at
    }
    
    item_agent_metadata {
        uuid id PK
        uuid item_id FK
        string category
        string importance
        jsonb metadata
    }
    
    action_proposals {
        uuid id PK
        uuid user_id FK
        string agent_name
        string action_type
        jsonb payload
        string status
        datetime created_at
    }
    
    execution_logs {
        uuid id PK
        uuid action_proposal_id FK
        string status
        text error_message
        datetime executed_at
    }
    
    user_preferences {
        uuid user_id PK
        string quiet_hours_start
        string quiet_hours_end
        jsonb preferred_work_blocks
        string email_tone
    }
    
    chat_sessions {
        uuid id PK
        uuid user_id FK
        datetime created_at
    }
    
    chat_messages {
        uuid id PK
        uuid session_id FK
        string sender
        text content
        jsonb metadata
        datetime timestamp
    }
```

### Core Tables

| Table | Purpose | Key Fields |
|-------|---------|------------|
| **users** | User accounts and authentication | `id`, `email`, `password_hash`, `timezone` |
| **connected_accounts** | OAuth provider connections | `user_id`, `provider`, `access_token`, `refresh_token` |
| **items** | Normalized emails and calendar events | `id`, `user_id`, `source_type`, `title`, `body_full` |
| **item_agent_metadata** | Agent-generated insights | `item_id`, `category`, `importance`, `metadata` |
| **action_proposals** | Proposed actions awaiting approval | `id`, `user_id`, `agent_name`, `action_type`, `status` |
| **execution_logs** | History of executed actions | `id`, `action_proposal_id`, `status`, `executed_at` |
| **user_preferences** | User settings and preferences | `user_id`, `quiet_hours_start`, `email_tone` |
| **preference_signals** | Feedback signals for learning | `id`, `user_id`, `signal_type`, `metadata` |
| **agent_run_logs** | Agent execution audit trail | `id`, `user_id`, `intent`, `execution_time_ms` |
| **chat_sessions** | Chat conversation sessions | `id`, `user_id`, `created_at` |
| **chat_messages** | Individual chat messages | `id`, `session_id`, `sender`, `content`, `timestamp` |

See [docs/database_schema.md](docs/database_schema.md) for detailed schema documentation.

---

## Configuration

### Environment Variables

```bash
# AI Provider
AI_PROVIDER=openai                    # or 'nvidia'
OPENAI_API_KEY=sk-...                 # Required if using OpenAI
OPENAI_MODEL=gpt-4o-mini              # OpenAI model name
NVIDIA_API_KEY=nvapi-...              # Required if using NVIDIA

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/ops_center

# OAuth (for integrations)
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
MICROSOFT_CLIENT_ID=...
MICROSOFT_CLIENT_SECRET=...

# Server
BACKEND_PORT=8001
FRONTEND_PORT=3001
```

See [env.example](env.example) for complete configuration options.

---

## Documentation

- [Architecture Overview](docs/architecture.md) - System design and components
- [Database Schema](docs/database_schema.md) - Detailed schema documentation
- [Integration Analysis](INTEGRATION_ANALYSIS.md) - NVIDIA GenerativeAIExamples patterns
- [Build Plan](buildplan.md) - Implementation roadmap
- [What's Next](WHATS_NEXT.md) - Future enhancements

---

## Contributing

We welcome contributions! Here's how to get started:

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. **Make your changes**
   - Follow code style guidelines
   - Add tests for new features
   - Update documentation
4. **Run quality checks**
   ```bash
   black --line-length=119 .
   flake8 . --max-line-length=119
   pytest
   ```
5. **Commit your changes**
   - Use clear, descriptive commit messages
   - Pre-commit hooks will run automatically
6. **Push and create a Pull Request**

### Development Guidelines

- Follow PEP 8 for Python code
- Use type hints where possible
- Write docstrings for all functions/classes
- Keep functions focused and small
- Add tests for new features
- Update README/docs for user-facing changes

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Support & Community

- **Issues**: [GitHub Issues](https://github.com/Sant0-9/Mini-os/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Sant0-9/Mini-os/discussions)

---

## Acknowledgments

- Built with [LangChain](https://www.langchain.com/) and [LangGraph](https://github.com/langchain-ai/langgraph)
- Inspired by [NVIDIA GenerativeAIExamples](https://github.com/NVIDIA/GenerativeAIExamples)
- Uses [FastAPI](https://fastapi.tiangolo.com/) for the backend
- Powered by [React](https://reactjs.org/) for the frontend

---

<div align="center">

**Built with ❤️ for personal productivity**

[⬆ Back to Top](#personal-ops-center)

</div>
