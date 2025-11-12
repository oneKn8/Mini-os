# Multi-Agent Personal Ops Center

A smart personal operations center that monitors Gmail, Outlook, Calendar, and weather to propose drafts and plans - but never acts without your approval.

## Project Status

Currently in Phase 0: Architecture and foundation setup.

## Repository Structure

```
multiagents/
├── backend/                     # Backend API and business logic (TBD)
├── orchestrator/                # Multi-agent orchestration layer (TBD)
├── frontend/                    # Web UI (TBD)
├── GenerativeAIExamples/        # NVIDIA reference implementations
├── .github/workflows/           # CI/CD pipelines
├── .git/hooks/                  # Git commit hooks
├── buildplan.md                 # Detailed phase-by-phase build plan
├── INTEGRATION_ANALYSIS.md      # Analysis of GenerativeAIExamples code
└── README.md                    # This file
```

## Features (Planned)

- Monitor Gmail and Outlook email accounts
- Track Google Calendar events
- Weather-aware planning
- AI-powered email triage and categorization
- Draft email responses (saved as drafts only)
- Propose calendar events and time blocks
- Smart daily and weekly planning
- Safety checks for scam detection
- Learning from user preferences

## Architecture Overview

### Three-Layer Design

1. **Frontend**: React SPA with Inbox, Today, Planner, Agent Console, and Settings views
2. **Backend API**: FastAPI-based REST API for auth, OAuth, data ingestion, action execution
3. **AI Orchestration**: Multi-agent system with specialized agents (Triage, Email, Planner, Safety, Preference)

### Key Principle

Agents **never** directly interact with external services. They only create structured `ActionProposal` records that require user approval before execution.

## Development Setup

### Prerequisites

- Python 3.10+
- Node.js 18+
- Docker and Docker Compose
- PostgreSQL 15+
- NVIDIA API Key (for LLM access)

### Installation

1. Clone the repository:
```bash
git clone <your-repo-url>
cd multiagents
```

2. Set up Python environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt  # Once we create it
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys and configuration
```

4. Install pre-commit hooks (automatically installed):
```bash
# The hooks are already in .git/hooks/
# They will run automatically on commit
```

## Git Hooks

This repository includes custom git hooks to ensure code quality:

### Pre-Commit Hook
- Checks for emojis in code
- Runs Python syntax validation
- Runs black formatter check (if installed)
- Runs flake8 linting (if installed)
- Runs ESLint for TypeScript/JavaScript (if installed)
- Runs TypeScript compiler check (if installed)

### Commit-Msg Hook
- Prevents emojis in commit messages
- Blocks references to "Claude" or "Anthropic" in commit messages

To bypass hooks in emergencies (not recommended):
```bash
git commit --no-verify -m "your message"
```

## CI/CD Pipeline

The project uses GitHub Actions for continuous integration:

- **Lint and Test**: Runs on Python 3.10 and 3.11
  - Black formatter check
  - Flake8 linting
  - MyPy type checking
  - Pytest with coverage

- **Frontend Lint**: 
  - ESLint
  - TypeScript compiler check
  - Build verification

- **Docker Build**:
  - Builds all Docker images
  - Runs health checks

- **Security Scan**:
  - Trivy vulnerability scanner
  - SARIF report upload to GitHub Security

## Using GenerativeAIExamples Code

We leverage NVIDIA's GenerativeAIExamples repository for:
- FastAPI server patterns
- Multi-agent orchestration with LangGraph
- OAuth integration patterns
- Docker deployment architecture

See `INTEGRATION_ANALYSIS.md` for detailed analysis and adaptation strategies.

## Development Workflow

### Adding New Features

1. Create a feature branch:
```bash
git checkout -b feature/your-feature-name
```

2. Make your changes, ensuring:
   - No emojis in code or commits
   - Code passes linting checks
   - Tests are added for new functionality

3. Commit your changes:
```bash
git add .
git commit -m "Add your feature description"
# Hooks will run automatically
```

4. Push and create a pull request:
```bash
git push origin feature/your-feature-name
```

### Code Style

- Python: Black formatter with line length 119
- TypeScript/JavaScript: ESLint with project configuration
- Follow PEP 8 for Python code
- Use meaningful variable and function names
- Add docstrings to all public functions and classes

## Build Plan Phases

See `buildplan.md` for the complete phased build plan. Summary:

- **Phase 0**: Project framing and architecture
- **Phase 1**: Data model and storage design
- **Phase 2**: Provider integrations (Gmail, Outlook, Calendar, Weather)
- **Phase 3**: Multi-agent orchestration skeleton
- **Phase 4**: Inbox triage agent
- **Phase 5**: Specialist agents (Email, Events, Weather)
- **Phase 6**: Planner agent
- **Phase 7**: Safety and scam agent
- **Phase 8**: Preference and feedback agent
- **Phase 9-11**: Frontend development
- **Phase 12**: Execution and error handling
- **Phase 13**: End-to-end integration

## Technology Stack

### Backend
- Python 3.10+
- FastAPI
- SQLAlchemy
- PostgreSQL
- LangGraph (for multi-agent orchestration)
- Pydantic (for validation)

### AI/ML
- NVIDIA NIM endpoints
- LangChain
- NVIDIA AI Endpoints

### Frontend
- React 18+
- TypeScript
- Tailwind CSS (planned)
- WebSocket or Server-Sent Events for streaming

### Infrastructure
- Docker and Docker Compose
- GitHub Actions
- PostgreSQL

### External Integrations
- Gmail API
- Microsoft Graph API (Outlook)
- Google Calendar API
- Weather API (OpenWeatherMap or similar)

## Environment Variables

Create a `.env` file with:

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/ops_center

# NVIDIA AI
NVIDIA_API_KEY=nvapi-your-key-here

# OAuth Credentials
GMAIL_CLIENT_SECRET_PATH=/path/to/gmail_client_secret.json
OUTLOOK_CLIENT_ID=your-outlook-client-id
OUTLOOK_CLIENT_SECRET=your-outlook-client-secret
GOOGLE_CALENDAR_CLIENT_SECRET_PATH=/path/to/calendar_client_secret.json

# Weather API
WEATHER_API_KEY=your-weather-api-key

# Application
SECRET_KEY=your-secret-key-for-jwt
ENVIRONMENT=development

# Feature Flags
ENABLE_TRACING=false
ENABLE_SAFETY_AGENT=true
ENABLE_PREFERENCE_LEARNING=true
```

## Testing

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

## Docker Deployment

```bash
# Build all services
docker-compose build

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

## Contributing

1. Read `buildplan.md` to understand the project architecture
2. Check `INTEGRATION_ANALYSIS.md` for patterns from GenerativeAIExamples
3. Ensure your code passes all git hooks and CI checks
4. Write tests for new functionality
5. Update documentation as needed

## Security

- Never commit API keys or secrets
- Use environment variables for sensitive data
- OAuth tokens are stored encrypted in the database
- All external API calls go through the executor layer after user approval

## License

[Add your license here]

## Acknowledgments

This project leverages patterns and code from:
- [NVIDIA GenerativeAIExamples](https://github.com/NVIDIA/GenerativeAIExamples)
- LangChain and LangGraph
- FastAPI
- React ecosystem

## Contact

[Add your contact information here]

