# Quick Start Guide - Personal Ops Center

Get up and running in 5 minutes!

## Step 1: Get Your OpenAI API Key

1. Go to https://platform.openai.com/api-keys
2. Click "Create new secret key"
3. Copy the key (starts with `sk-...`)

## Step 2: Configure

```bash
# Copy the example environment file
cp env.example .env

# Edit .env and add your key
nano .env  # or use your favorite editor
```

Add this line:
```
OPENAI_API_KEY=sk-your-actual-key-here
AI_PROVIDER=openai
```

## Step 3: Test It

```bash
# Test your API key works
python test_openai.py
```

You should see `[SUCCESS] ALL TESTS PASSED!`

## Step 4: Start Everything

```bash
./start.sh
```

Wait for services to start (~30 seconds).

## Step 5: Open The App

Open in your browser:
- **Frontend**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs

That's it! You're running!

---

## What To Do Next

1. **Connect Your Email** (OAuth setup - see docs)
2. **Let It Process** - Agents will triage your inbox
3. **Review Actions** - Approve/reject proposed actions
4. **Check Today View** - See your daily plan

---

## Management Commands

```bash
./start.sh      # Start everything
./stop.sh       # Stop everything
./restart.sh    # Restart
./logs.sh       # View logs
./status.sh     # Check health
```

---

## Troubleshooting

**Services won't start?**
```bash
./stop.sh
docker-compose down -v
./start.sh
```

**API key issues?**
```bash
# Check .env file
cat .env | grep OPENAI

# Test again
python test_openai.py
```

**Need help?**
```bash
./status.sh  # Check what's running
./logs.sh    # See what's happening
```

---

## Full Documentation

- **Setup Guide**: See `OPENAI_SETUP.md`
- **Scripts Guide**: See `SCRIPTS_GUIDE.md`
- **Architecture**: See `docs/architecture.md`
- **Build Details**: See `BUILD_COMPLETE.md`

Enjoy your Personal Ops Center!
