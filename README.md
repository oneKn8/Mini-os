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

| Agent | Purpose | Capabilities |
|-------|---------|--------------|
| **Triage Agent** | Classification & Prioritization | Categorizes emails, assigns importance, extracts deadlines |
| **Email Agent** | Content Generation | Summarizes emails, drafts replies, respects tone preferences |
| **Event Agent** | Calendar Management | Extracts events, proposes calendar entries, detects deadlines |
| **Planner Agent** | Daily Planning | Generates time blocks, suggests focus areas, considers context |
| **Safety Agent** | Security & Risk | Detects phishing, assesses action risks, flags suspicious content |
| **Preference Agent** | Learning & Adaptation | Learns from feedback, updates preferences, improves recommendations |

### Technology Stack

**Frontend**
- React 18 with TypeScript
- Vite for fast development
- Modern, minimalist UI design
- Responsive and accessible

**Backend**
- FastAPI with async/await
- SQLAlchemy ORM
- Alembic migrations
- RESTful API design

**AI & Orchestration**
- LangChain for LLM integration
- LangGraph for multi-agent workflows
- Support for OpenAI and NVIDIA NIM
- State-based agent coordination

**Database**
- PostgreSQL
- JSONB for flexible metadata
- Optimized indexes
- Full-text search support

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

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend (React)                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │  Today   │  │  Inbox   │  │ Planner  │  │   Chat   │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
└──────────────────────┬────────────────────────────────────┘
                       │ HTTP/REST
┌──────────────────────▼────────────────────────────────────┐
│              Backend API (FastAPI)                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │  Inbox   │  │ Planner  │  │ Actions  │  │   Sync   │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
└──────────────────────┬────────────────────────────────────┘
                       │
┌──────────────────────▼────────────────────────────────────┐
│         Orchestrator (LangGraph)                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │  Triage  │  │  Email   │  │  Event   │  │ Planner  │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
│  ┌──────────┐  ┌──────────┐                              │
│  │  Safety  │  │Preference│                              │
│  └──────────┘  └──────────┘                              │
└──────────────────────┬────────────────────────────────────┘
                       │
┌──────────────────────▼────────────────────────────────────┐
│         LLM Client (LangChain)                             │
│  ┌──────────┐              ┌──────────┐                   │
│  │  OpenAI  │              │  NVIDIA  │                   │
│  └──────────┘              └──────────┘                   │
└────────────────────────────────────────────────────────────┘
```

### Agent Workflow (LangGraph)

The orchestrator uses **LangGraph** to manage agent execution:

```
Intent: refresh_inbox
  │
  ├─► Triage Agent (classify & prioritize)
  │     │
  ├─► Safety Agent (detect scams)
  │     │
  ├─► Email Agent (summarize & draft)
  │     │
  └─► Event Agent (extract events)
        │
        └─► Action Proposals → Database
```

### Data Flow

1. **Ingestion**: OAuth clients fetch emails/events from providers
2. **Normalization**: Data stored in unified `items` table
3. **Orchestration**: LangGraph workflow routes to appropriate agents
4. **Processing**: Agents generate metadata and action proposals
5. **Storage**: Results stored in database with full audit trail
6. **Presentation**: Frontend displays processed data and proposals

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

```
multiagents/
├── backend/
│   ├── api/
│   │   ├── models/          # SQLAlchemy models
│   │   ├── routes/          # API endpoints
│   │   └── server.py        # FastAPI app
│   ├── integrations/       # OAuth clients (Gmail, Outlook, Calendar)
│   ├── ingestion/           # Data sync services
│   └── executor/            # Action execution
├── orchestrator/
│   ├── agents/              # Agent implementations
│   ├── state.py             # LangGraph state model
│   └── orchestrator.py      # LangGraph workflow
├── frontend/
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── pages/           # Route pages
│   │   └── api/             # API clients
│   └── package.json
├── tests/                   # Test suite
├── alembic/                 # Database migrations
└── docs/                    # Documentation
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

### Core Tables

- **users** - User accounts and authentication
- **connected_accounts** - OAuth provider connections
- **items** - Normalized emails and calendar events
- **item_agent_metadata** - Agent-generated insights and classifications
- **action_proposals** - Proposed actions awaiting user approval
- **execution_logs** - History of executed actions
- **user_preferences** - User settings and preferences
- **preference_signals** - Feedback signals for learning
- **agent_run_logs** - Agent execution audit trail
- **chat_sessions** - Chat conversation sessions
- **chat_messages** - Individual chat messages

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
