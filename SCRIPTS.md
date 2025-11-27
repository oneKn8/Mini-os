# Script Reference Guide

Quick reference for all available scripts in this project.

## Main Workflow Scripts

### Native PostgreSQL Setup (Recommended)
```bash
./start.sh    # Start backend + frontend (uses PostgreSQL on port 5433)
./stop.sh     # Stop all services
./restart.sh  # Restart services
./status.sh   # Check running services
./logs.sh     # View application logs
```

### Docker Setup (Alternative)
```bash
./start_local.sh  # Start backend + frontend + Docker PostgreSQL (port 5643)
./stop_local.sh   # Stop all services including Docker
```

## Setup & Configuration Scripts

### Initial Setup
```bash
./setup_postgres.sh           # Set up PostgreSQL database
./create_tables.sh           # Create database tables
./fix_postgres.sh            # Fix PostgreSQL connection issues
```

### OAuth Configuration
```bash
./setup_google_oauth.sh      # Interactive OAuth setup
./get_oauth_credentials.sh   # Get OAuth credentials
./guide_google_setup.sh      # Detailed OAuth setup guide
```

### Development
```bash
./dev.sh                     # Development mode with hot reload
```

## Port Configuration

| Service    | Native Setup | Docker Setup |
|------------|--------------|--------------|
| Database   | 5433         | 5643         |
| Backend    | 8101         | 8101         |
| Frontend   | 3101         | 3101         |

## Environment Files

- `.env` - Main configuration (edit this for your setup)
- `env.example` - Template for environment variables

## Log Files

- `backend.log` - Backend application logs
- `frontend.log` - Frontend development server logs

## PID Files (Auto-generated)

- `.native.pid` - Process IDs for native setup
- `.local.pid` - Process IDs for Docker setup

**Note:** PID files are automatically managed by start/stop scripts. Don't edit manually.

## Common Tasks

### Check if services are running
```bash
./status.sh
# OR
lsof -i:8101,3101,5433
```

### View real-time logs
```bash
tail -f backend.log
tail -f frontend.log
# OR
./logs.sh
```

### Full restart
```bash
./stop.sh && ./start.sh
# OR
./restart.sh
```

### Switch between Native and Docker
```bash
# Stop current setup
./stop.sh  # or ./stop_local.sh

# Start desired setup
./start.sh  # for native PostgreSQL
# OR
./start_local.sh  # for Docker PostgreSQL
```

## Troubleshooting

### Port already in use
```bash
# Find process using port
lsof -ti:8101  # or 3101, 5433

# Kill process
kill -9 $(lsof -ti:8101)

# Or use stop script
./stop.sh
```

### Database connection errors
```bash
./fix_postgres.sh
```

### OAuth setup issues
```bash
./guide_google_setup.sh  # Follow the interactive guide
```
