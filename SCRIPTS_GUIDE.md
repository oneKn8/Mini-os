# Personal Ops Center - Scripts Guide

Quick reference for all management scripts.

## Main Scripts

### 🚀 `./start.sh`
Start PostgreSQL (via systemd), run migrations, and launch the backend + frontend locally.

```bash
./start.sh
```

**What it does:**
- Ensures a `.env` file exists (creates one from `env.example` if needed)
- Starts the local PostgreSQL service via `systemctl` if it's not running
- Runs Alembic migrations against `postgresql://ops_user:ops_password@localhost:5543/ops_center`
- Launches the FastAPI backend with `uvicorn` (logs to `backend.log`)
- Launches the Vite dev server for the frontend (logs to `frontend.log`)
- Stores process IDs in `.native.pid` for easy shutdown later

**Access points after starting:**
- Frontend: http://localhost:3101
- API: http://localhost:8101
- API Docs: http://localhost:8101/docs
- Health: http://localhost:8101/health

---

### 🛑 `./stop.sh`
Stop the uvicorn and Vite processes started by `./start.sh`.

```bash
./stop.sh
```

**What it does:**
- Reads `.native.pid` and kills the recorded backend/frontend processes
- Falls back to `pkill` if the PID file is missing
- Leaves PostgreSQL running (use `sudo systemctl stop postgresql` if you really need to stop the DB)

---

### 🔄 `./restart.sh`
Restart all services.

```bash
./restart.sh
```

Equivalent to: `./stop.sh && ./start.sh`

---

### 📊 `./logs.sh`
View Docker service logs (use `backend.log` / `frontend.log` when running via `./start.sh`).

```bash
# All services
./logs.sh

# Specific service
./logs.sh backend-api
./logs.sh frontend
./logs.sh postgres
```

Press `Ctrl+C` to exit.

---

### 🔍 `./status.sh`
Check Docker system status. (For native runs, hit `/health` and tail the local logs instead.)

```bash
./status.sh
```

**Shows:**
- Docker services running
- Database health
- Backend API health
- Frontend health

---

### 🔧 `./dev.sh`
Development mode with hot reload.

```bash
./dev.sh
```

**What it does:**
- Starts database in Docker
- Runs backend locally with uvicorn (hot reload)
- Runs frontend locally with Vite (hot reload)
- Logs to `backend.log` and `frontend.log`

**Requirements:**
- Python dependencies installed: `pip install -r requirements.txt`
- Node dependencies installed: `cd frontend && npm install`

**To stop:**
```bash
# Check PIDs
cat .dev.pid

# Kill processes
kill $(cat .dev.pid)
docker-compose stop postgres
```

---

## Quick Start

### First Time Setup

1. **Clone and setup:**
   ```bash
   git clone <repo>
   cd multiagents
   cp env.example .env
   # Edit .env and add NVIDIA_API_KEY
   ```

2. **Start everything:**
   ```bash
   ./start.sh
   ```

3. **Access the app:**
   - Open http://localhost:3101

### Daily Development

**Everyday usage (native processes):**
```bash
./start.sh        # Start
tail -f backend.log   # Backend logs
tail -f frontend.log  # Frontend logs
./stop.sh         # Stop backend/frontend
```

**Development mode (hot reload):**
```bash
./dev.sh          # Start with hot reload
tail -f backend.log   # Watch backend logs
tail -f frontend.log  # Watch frontend logs
```

---

## Troubleshooting

### Services won't start

```bash
# Make sure PostgreSQL is running
sudo systemctl status postgresql

# Kill any stuck processes
./stop.sh
pkill -f "uvicorn backend.api.server:app" 2>/dev/null || true
pkill -f "vite" 2>/dev/null || true

# Clean restart
./start.sh
```

### Database issues

```bash
# Connect directly
psql postgresql://ops_user:ops_password@localhost:5543/ops_center

# Re-run migrations if needed
alembic upgrade head
```

### Frontend not loading

```bash
# Check frontend log
tail -f frontend.log

# Restart frontend only
pkill -f "vite"
(cd frontend && npm run dev >> ../frontend.log 2>&1 &)
```

### Backend API errors

```bash
# Check backend logs
./logs.sh backend-api

# Check environment variables
docker-compose exec backend-api env | grep -E 'NVIDIA|DATABASE'

# Rebuild backend
docker-compose up -d --build backend-api
```

---

## Environment Variables

Required in `.env`:

```bash
# Required
NVIDIA_API_KEY=your_key_here

# Optional (have defaults)
POSTGRES_USER=ops_user
POSTGRES_PASSWORD=changeme
POSTGRES_DB=ops_center
ENVIRONMENT=development
LOG_LEVEL=INFO
```

---

## Docker Commands Reference

```bash
# View running containers
docker-compose ps

# View all logs
docker-compose logs -f

# Restart specific service
docker-compose restart backend-api

# Rebuild and restart
docker-compose up -d --build backend-api

# Enter container shell
docker-compose exec backend-api bash

# Run migrations manually
docker-compose exec backend-api alembic upgrade head

# Database shell
docker-compose exec postgres psql -U ops_user -d ops_center

# Remove everything (including data)
docker-compose down -v
```

---

## Testing

```bash
# Run tests in Docker
docker-compose exec backend-api pytest

# Run tests locally
pytest

# Run with coverage
pytest --cov=backend --cov=orchestrator
```

---

## Common Workflows

### Adding a new agent

1. Create agent file: `orchestrator/agents/new_agent.py`
2. Register in orchestrator: `orchestrator/orchestrator.py`
3. Test: `pytest tests/test_orchestrator.py`
4. Restart: `./restart.sh`

### Updating database schema

1. Modify models: `backend/api/models/`
2. Create migration: `docker-compose exec backend-api alembic revision --autogenerate -m "description"`
3. Apply migration: `docker-compose exec backend-api alembic upgrade head`

### Frontend changes

In Docker (auto-reload):
```bash
# Changes auto-reload
./logs.sh frontend
```

Local dev:
```bash
cd frontend
npm run dev
```

### Backend changes

In Docker (auto-reload enabled):
```bash
# Changes auto-reload
./logs.sh backend-api
```

Local dev:
```bash
./dev.sh
# or
uvicorn backend.api.server:app --reload
```

---

## Production Deployment

For production, you'll want to:

1. **Use production Dockerfile** (multi-stage build)
2. **Set environment variables** properly
3. **Use secrets management** (not .env file)
4. **Add reverse proxy** (nginx/traefik)
5. **Enable HTTPS**
6. **Configure logging** (external aggregation)
7. **Set resource limits** in docker-compose
8. **Use orchestration** (Kubernetes/Docker Swarm)

Example production docker-compose snippet:
```yaml
services:
  backend-api:
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '1'
          memory: 1G
    restart: always
```

---

## Getting Help

```bash
# Check system status
./status.sh

# View logs
./logs.sh

# Check environment
docker-compose exec backend-api env

# Test API
curl http://localhost:8101/health
```

For issues, check:
1. Logs: `./logs.sh`
2. Status: `./status.sh`
3. Environment: `.env` file
4. Ports: 3101 (frontend), 8101 (API), 5543/5643 (Postgres) available
5. Docker: daemon running

---

## Summary

| Script | Purpose | When to Use |
|--------|---------|-------------|
| `start.sh` | Start all services | First time, production-like testing |
| `stop.sh` | Stop all services | End of work, cleanup |
| `restart.sh` | Restart everything | After config changes |
| `logs.sh` | View logs | Debugging, monitoring |
| `status.sh` | Check health | Quick health check |
| `dev.sh` | Development mode | Active development with hot reload |

**Most common workflow:**
```bash
./start.sh    # Morning
./logs.sh     # Monitor
./stop.sh     # Evening
```
