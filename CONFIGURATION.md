# Configuration Guide

## Quick Start

1. **Copy the template:**
   ```bash
   cp .env.example .env
   ```

2. **Fill in your API keys:**
   ```bash
   # Edit .env file
   OPENAI_API_KEY=sk-your-real-key-here
   GROQ_API_KEY=gsk_your-real-key-here
   ```

3. **That's it!** The application will automatically load from `.env`

## Configuration Methods (Priority Order)

### 1. Environment Variables (Highest Priority)

Set at runtime - used in production:

```bash
export OPENAI_API_KEY="sk-your-key"
export GROQ_API_KEY="gsk_your-key"
python demo/cli_demo.py
```

### 2. .env File (Local Development)

Create `.env` in project root:

```bash
OPENAI_API_KEY=sk-your-key
GROQ_API_KEY=gsk_your-key
```

### 3. Default Values (Lowest Priority)

Some configs have sensible defaults (see `MovieAgentConfig`).

## Required Configuration

### API Keys

| Variable | Required | Description | Where to Get |
|----------|----------|-------------|--------------|
| `OPENAI_API_KEY` | ✅ Yes | OpenAI API key for embeddings | [OpenAI Dashboard](https://platform.openai.com/api-keys) |
| `GROQ_API_KEY` | ✅ Yes | Groq API key for LLM | [Groq Console](https://console.groq.com/keys) |

## Optional Configuration

### Data Paths

| Variable | Default | Description |
|----------|---------|-------------|
| `MOVIE_DATA_CSV_PATH` | `data/movies.csv` | Path to movies CSV file |
| `VECTOR_STORE_PATH` | `movie_vectorstore` | Path to FAISS vector store directory |

### LLM Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_PROVIDER` | `groq` | LLM provider: `groq` or `openai` |
| `LLM_MODEL` | `llama-3.1-8b-instant` | Model name (see provider docs) |

### Vision Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `ENABLE_VISION` | `false` | Enable poster analysis |
| `VISION_MODEL_NAME` | `Salesforce/blip-image-captioning-base` | BLIP model name |
| `VISION_MODEL_PATH` | `None` | Optional local model path |

### Semantic Resolution

| Variable | Default | Description |
|----------|---------|-------------|
| `ENABLE_FUZZY_MATCHING` | `true` | Enable query typo correction |
| `FUZZY_THRESHOLD` | `0.75` | Minimum fuzzy match score (0.0-1.0) |
| `RESOLUTION_CONFIDENCE_THRESHOLD` | `0.75` | Minimum resolution confidence (0.0-1.0) |

## Production Deployment

### Environment Variables (Recommended)

Set in your deployment platform:

**Heroku:**
```bash
heroku config:set OPENAI_API_KEY=sk-your-key
heroku config:set GROQ_API_KEY=gsk_your-key
```

**Docker:**
```dockerfile
ENV OPENAI_API_KEY=sk-your-key
ENV GROQ_API_KEY=gsk_your-key
```

**Kubernetes:**
```yaml
env:
  - name: OPENAI_API_KEY
    valueFrom:
      secretKeyRef:
        name: movie-agent-secrets
        key: openai-api-key
```

### Secrets Management Services

For production, use proper secrets management:

- **AWS Secrets Manager**
- **HashiCorp Vault**
- **Azure Key Vault**
- **Google Secret Manager**

## Security Best Practices

1. ✅ **Never commit `.env` to git** (already in `.gitignore`)
2. ✅ **Use `.env.example` as template** (safe to commit)
3. ✅ **Rotate keys regularly**
4. ✅ **Use different keys for dev/prod**
5. ✅ **Never log API keys** (masked in error messages)
6. ✅ **Use least privilege** (minimal permissions)

## Troubleshooting

### "OPENAI_API_KEY not set"

**Solution:**
1. Check `.env` file exists in project root
2. Verify key is set: `echo $OPENAI_API_KEY`
3. Ensure `.env` is loaded: `load_dotenv()` is called
4. Check for typos in variable name

### "API key appears to be a placeholder"

**Solution:**
- Replace placeholder values in `.env` with real API keys
- Get keys from provider dashboards (see table above)

### Configuration not loading

**Solution:**
1. Verify `.env` file location (project root)
2. Check file permissions
3. Ensure `python-dotenv` is installed: `pip install python-dotenv`
4. Verify `load_dotenv()` is called before config access

