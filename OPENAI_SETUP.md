# OpenAI API Setup Guide

The Personal Ops Center now supports **both OpenAI and NVIDIA NIM** for LLM capabilities!

## Quick Setup (OpenAI)

### 1. Get your OpenAI API Key

1. Go to https://platform.openai.com/api-keys
2. Click "Create new secret key"
3. Copy your API key (starts with `sk-...`)

### 2. Configure your `.env` file

```bash
# Copy the example file
cp env.example .env

# Edit .env and add your API key
AI_PROVIDER=openai
OPENAI_API_KEY=sk-your-actual-api-key-here
OPENAI_MODEL=gpt-4o-mini
```

### 3. Test the integration

```bash
# Install dependencies first (if not using Docker)
pip install -r requirements.txt

# Run the test script
python test_openai.py
```

You should see:
```
✅ ALL TESTS PASSED!
Your OpenAI API is working correctly!
```

### 4. Start the system

```bash
./start.sh
```

That's it! Your system is now using OpenAI.

---

## Alternative: NVIDIA NIM Setup

If you prefer to use NVIDIA's open-source models:

```bash
# In .env file
AI_PROVIDER=nvidia
NVIDIA_API_KEY=nvapi-your-nvidia-key-here
```

Get NVIDIA API key from: https://build.nvidia.com/

---

## Model Comparison

| Feature | OpenAI (GPT-4o-mini) | NVIDIA NIM (Llama 3 70B) |
|---------|----------------------|--------------------------|
| **Speed** | Very Fast (~1-2s) | Fast (~2-3s) |
| **Reliability** | Excellent (99.9% uptime) | Good (95%+ uptime) |
| **JSON Parsing** | Excellent | Good (sometimes needs cleanup) |
| **Cost** | $0.150 per 1M input tokens | Free (for now) |
| **Quality** | Excellent | Very Good |
| **Recommended** | ✅ Production use | Development/Testing |

### Recommendation

**For production**: Use OpenAI (gpt-4o-mini)
- More reliable
- Better JSON parsing
- Faster responses
- Predictable costs

**For development**: Either works great!

---

## Switching Providers

You can switch between providers anytime:

### In Docker:

Edit `.env`:
```bash
# Switch to OpenAI
AI_PROVIDER=openai
OPENAI_API_KEY=sk-your-key

# OR switch to NVIDIA
AI_PROVIDER=nvidia
NVIDIA_API_KEY=nvapi-your-key
```

Then restart:
```bash
./restart.sh
```

### In Local Development:

```bash
# Export environment variable
export AI_PROVIDER=openai
export OPENAI_API_KEY=sk-your-key

# Restart backend
uvicorn backend.api.server:app --reload
```

---

## Testing Both Providers

You can have both API keys configured:

```bash
# .env file
AI_PROVIDER=openai  # Currently active

OPENAI_API_KEY=sk-your-openai-key
NVIDIA_API_KEY=nvapi-your-nvidia-key
```

Test each provider:

```bash
# Test OpenAI
export AI_PROVIDER=openai
python test_openai.py

# Test NVIDIA
export AI_PROVIDER=nvidia
python test_openai.py
```

---

## Cost Estimates

### OpenAI (gpt-4o-mini)

Typical usage per day:
- 100 emails processed: ~50,000 tokens input, ~5,000 tokens output
- Cost: ~$0.01 per day
- Monthly: ~$0.30

**Very affordable for personal use!**

### NVIDIA NIM

Currently free for API access. May have rate limits.

---

## Troubleshooting

### "API key not found"

```bash
# Check if .env file exists
cat .env

# Check if variable is set
echo $OPENAI_API_KEY

# Reload environment
source .env  # (bash)
```

### "OpenAI API error: 401 Unauthorized"

Your API key is invalid. Check:
1. Copied the full key (starts with `sk-`)
2. No extra spaces or quotes in `.env`
3. API key is active (check OpenAI dashboard)

### "Rate limit exceeded"

OpenAI free tier limits:
- 3 requests per minute
- 200 requests per day

Upgrade to paid tier for higher limits (still very cheap).

### "Model not found"

Make sure you're using a valid model name:
- `gpt-4o-mini` (recommended, fast & cheap)
- `gpt-4o` (more capable, more expensive)
- `gpt-3.5-turbo` (older, cheaper)

---

## Advanced Configuration

### Custom Model

```bash
# In .env
OPENAI_MODEL=gpt-4o  # More capable but slower
```

### Adjust Temperature

Agents have preset temperatures:
- Triage: 0.2 (deterministic)
- Safety: 0.1 (very deterministic)
- Email: 0.3 (slightly creative)
- Planner: 0.4 (more creative)

To change, edit agent files in `orchestrator/agents/`.

### Custom API Endpoint

For Azure OpenAI or other compatible APIs:

Edit `orchestrator/llm_client.py`:
```python
self.api_url = "https://your-azure-endpoint.openai.azure.com/..."
```

---

## FAQ

**Q: Do I need both API keys?**
A: No, just one! Choose either OpenAI or NVIDIA.

**Q: Can I switch providers without losing data?**
A: Yes! Your data is stored in PostgreSQL. Switching providers only affects how agents process new items.

**Q: Which is better for my use case?**
A: For production and reliability: OpenAI. For experimentation and cost-free: NVIDIA.

**Q: Will my API calls be private?**
A: OpenAI: Data not used for training by default. Check their privacy policy.
NVIDIA: Check NVIDIA Build privacy policy.

**Q: Can I use a local LLM?**
A: Yes! You can modify `llm_client.py` to support Ollama, LM Studio, or any OpenAI-compatible API.

---

## Next Steps

1. ✅ Set up API key
2. ✅ Test with `test_openai.py`
3. ✅ Start the system: `./start.sh`
4. 🌐 Open http://localhost:3000
5. 📧 Connect your email accounts (OAuth)
6. 🤖 Let the agents work for you!

---

## Support

Issues with OpenAI API? Check:
- OpenAI Status: https://status.openai.com/
- OpenAI Docs: https://platform.openai.com/docs
- Our logs: `./logs.sh backend-api`

For NVIDIA NIM issues:
- NVIDIA Build: https://build.nvidia.com/
- Our logs: `./logs.sh backend-api`

