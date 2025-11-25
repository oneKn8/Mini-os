# Personal Ops Center

A multi-agent AI system for managing emails, calendar events, and daily planning with intelligent automation.

## Features

- **Multi-Agent System**: Triage, Email, Event, Planner, Safety, and Preference Learning agents
- **Email & Calendar Integration**: OAuth support for Gmail, Outlook, and Google Calendar
- **Intelligent Triage**: Automatic classification, importance scoring, and action suggestions
- **Daily Planning**: AI-powered daily plans with time blocks and focus areas
- **Safety Checks**: Scam detection and action risk assessment
- **Preference Learning**: Learns from user feedback to improve recommendations
- **Modern UI**: React-based frontend with dark theme and responsive design

## Architecture

- **Frontend**: React 18 + TypeScript + Vite
- **Backend API**: FastAPI + SQLAlchemy
- **Orchestrator**: Multi-agent coordination layer
- **Database**: PostgreSQL with Alembic migrations
- **AI**: NVIDIA NIM (Llama 3 70B)

## Quick Start

### Prerequisites

- Docker & Docker Compose
- AI Provider API Key:
  - OpenAI API Key (recommended: GPT-4o-mini), OR
  - NVIDIA NIM API Key (Llama 3 70B)

### Setup

1. Clone the repository:

```bash
git clone https://github.com/Sant0-9/Mini-os
cd multiagents
```

2. Create environment file:

```bash
cp env.example .env
# Edit .env and add your API key:
# - For OpenAI: Set OPENAI_API_KEY and AI_PROVIDER=openai
# - For NVIDIA: Set NVIDIA_API_KEY and AI_PROVIDER=nvidia
```

3. Start services:

```bash
docker-compose up -d
```

4. Run database migrations:

```bash
docker-compose exec backend alembic upgrade head
```

5. Access the application:
   - Frontend: http://localhost:3101
   - API Docs: http://localhost:8101/docs
   - Health Check: http://localhost:8101/health

## Development

### Backend Development

```bash
cd backend
pip install -r ../requirements.txt
uvicorn backend.api.server:app --reload
```

### Frontend Development

```bash
cd frontend
npm install
npm run dev
```

### Running Tests

```bash
pytest
```

### Code Quality

All commits are automatically checked for:
- Python: Black formatting (line length 119), Flake8 linting
- TypeScript: ESLint, TypeScript compilation
- Commit messages: No emojis or specific keywords

## API Endpoints

### Inbox
- `GET /api/inbox` - Get inbox items (filterable)
- `GET /api/inbox/{item_id}` - Get single item

### Planner
- `GET /api/planner/today` - Get today's plan

### Actions
- `GET /api/actions/pending` - Get pending actions
- `POST /api/actions/{id}/approve` - Approve action
- `POST /api/actions/{id}/reject` - Reject action

### Sync
- `POST /api/sync/trigger` - Trigger data sync

## Agents

### Triage Agent
- Classifies emails/events into categories
- Assigns importance levels (critical, high, medium, low, ignore)
- Extracts due dates and entities
- Suggests actions (reply, attend, pay, read, etc.)

### Email Agent
- Generates email summaries
- Creates draft replies
- Respects user's tone preferences

### Event Agent
- Extracts calendar events from emails
- Proposes event creation
- Detects deadlines

### Planner Agent
- Generates daily plans
- Suggests time blocks
- Considers weather and user preferences

### Safety Agent
- Detects phishing and scams
- Assesses action risk levels
- Flags suspicious content

### Preference Agent
- Learns from user feedback
- Updates preferences automatically
- Improves recommendations over time

## Database Schema

Core tables:
- `users` - User accounts
- `connected_accounts` - OAuth connections
- `items` - Normalized emails/events
- `item_agent_metadata` - Agent-generated insights
- `action_proposals` - Proposed actions awaiting approval
- `execution_logs` - Action execution history
- `user_preferences` - User settings
- `preference_signals` - Feedback signals
- `agent_run_logs` - Agent activity logs

## License

MIT License

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## Support

For issues and questions, please open a GitHub issue.
