# Hugging Face Spaces Deployment Guide

Complete guide for deploying Movie Agent Service to Hugging Face Spaces using Docker and Flask.

## Architecture Overview

- **`movie-agent-service/`**: Pure library/service (no UI components)
- **`movie-agent-demo/`**: Flask application with templates/static (uses the service)

For deployment, we copy:
- Service code from `movie-agent-service/src`
- Flask app from `movie-agent-service/app.py` (deployment artifact)
- Templates/static from `movie-agent-demo/` (application layer)

## Prerequisites

1. Hugging Face account at https://huggingface.co
2. API keys:
   - Groq API key: https://console.groq.com
   - OpenAI API key: https://platform.openai.com (for embeddings)

## Step 1: Create Space on Hugging Face

1. Go to https://huggingface.co/spaces
2. Click **"Create new Space"**
3. Configure:
   - **Space name**: `movie-agent-service` (or your preferred name)
   - **SDK**: Select **Docker** (NOT Gradio!)
   - **Visibility**: Public or Private
4. Click **"Create Space"**

## Step 2: Clone Your Space Repository

Open Terminal and run:

```bash
# Go to your projects directory
cd /Users/admin/Desktop/projects/MovieOOP

# Clone your Space (replace ABZanganeh with YOUR username)
git clone https://huggingface.co/spaces/ABZanganeh/movie-agent-service hf-space

# Go into the cloned directory
cd hf-space
```

**Directory Structure:**
```
/Users/admin/Desktop/projects/MovieOOP/
├── movie-agent-service/     ← Your service code
└── hf-space/                ← Your Space repo (clone goes here)
```

## Step 3: Copy Files to Space Repository

While in the `hf-space` directory, copy files:

```bash
# Copy Dockerfile
cp ../movie-agent-service/Dockerfile ./

# Copy Flask app (deployment artifact)
cp ../movie-agent-service/app.py ./

# Copy requirements
cp ../movie-agent-service/requirements.txt ./

# Copy service source code
cp -r ../movie-agent-service/src ./

# Copy templates (from movie-agent-demo - application layer)
cp -r ../movie-agent-demo/templates ./

# Copy static files (from movie-agent-demo - application layer)
cp -r ../movie-agent-demo/static ./

# Copy data
cp -r ../movie-agent-service/data ./

# Copy vector store (optional, speeds up first build)
cp -r ../movie-agent-service/movie_vectorstore ./ 2>/dev/null || echo "Vector store will be built on first run"
```

**What you're copying:**
- From `movie-agent-service/`: Dockerfile, app.py, requirements.txt, src/, data/
- From `movie-agent-demo/`: templates/, static/ (UI components)

## Step 4: Verify Files

```bash
# Check all files are present
ls -la

# You should see:
# - Dockerfile
# - app.py
# - requirements.txt
# - src/ (directory)
# - templates/ (directory)
# - static/ (directory)
# - data/ (directory)
# - movie_vectorstore/ (directory, if copied)
```

## Step 5: Commit and Push

```bash
# Check status
git status

# Add all files
git add .

# Commit
git commit -m "Initial Flask deployment"

# Push to Hugging Face
git push
```

The Space will automatically start building (check the **Logs** tab).

## Step 6: Configure Environment Variables

1. Go to your Space page: `https://huggingface.co/spaces/ABZanganeh/movie-agent-service`
2. Click **Settings** (gear icon)
3. Click **Repository secrets** in the left menu
4. Add secrets (click "New secret" for each):

   **Required:**
   - **Name**: `GROQ_API_KEY`
     **Value**: Your Groq API key from https://console.groq.com
     Click **Save secret**

   - **Name**: `OPENAI_API_KEY`
     **Value**: Your OpenAI API key from https://platform.openai.com
     Click **Save secret**

   **Optional:**
   - `LLM_PROVIDER`: `"groq"` or `"openai"` (default: `"groq"`)
   - `LLM_MODEL`: Model name (default: `"llama-3.1-8b-instant"`)
   - `ENABLE_VISION`: `"true"` or `"false"` (default: `"true"`)
   - `ENABLE_MEMORY`: `"true"` or `"false"` (default: `"true"`)
   - `DEVICE`: `"auto"`, `"cpu"`, `"cuda"`, or `"mps"` (default: `"auto"`)
   - `FORCE_CPU`: `"true"` or `"false"` (default: `"false"`)

5. Go to the **App** tab

## Step 7: Wait for Build and Test

- **First build**: Takes 5-10 minutes (builds vector store if not pre-built)
- **Check progress**: Monitor the **Logs** tab
- **When complete**: Your Flask app will be accessible in the **App** tab
- **Test**: Try the chat and poster upload features

## Troubleshooting

### Build Fails

- **Check logs**: Review the **Logs** tab for errors
- **Verify files**: Ensure all files were copied correctly
- **Check requirements.txt**: All dependencies should be listed

### App Fails to Start

- **API keys**: Verify secrets are set correctly in Settings
- **Check logs**: Look for initialization errors
- **Data files**: Ensure `data/movies.csv` exists

### Templates Not Found

- **Verify copy**: Check that templates/ and static/ directories exist
- **Source**: Templates should come from `movie-agent-demo/`, not `movie-agent-service/`

### Vector Store Build Time

- **First run**: Vector store builds automatically (takes a few minutes)
- **Speed up**: Copy pre-built `movie_vectorstore/` directory to skip build
- **Check logs**: Vector store build progress is visible in logs

### Port Issues

- **Automatic**: Hugging Face Spaces sets `PORT` environment variable automatically
- **Don't hardcode**: App reads `PORT` from environment (default: 7860)

## Updating Your Deployment

To update after making changes:

```bash
# Make changes to your code

# Go to Space repository
cd /Users/admin/Desktop/projects/MovieOOP/hf-space

# Copy updated files
cp ../movie-agent-service/app.py ./
cp ../movie-agent-service/requirements.txt ./
cp -r ../movie-agent-service/src ./
cp -r ../movie-agent-demo/templates ./
cp -r ../movie-agent-demo/static ./

# Commit and push
git add .
git commit -m "Update: description of changes"
git push
```

The Space will automatically rebuild (2-5 minutes).

## File Structure in Space

```
hf-space/
├── Dockerfile              ← Docker configuration
├── app.py                  ← Flask application
├── requirements.txt        ← Python dependencies
├── src/                    ← Service source code
│   └── movie_agent/
├── templates/              ← HTML templates (from movie-agent-demo)
│   ├── index.html
│   ├── about.html
│   └── setup.html
├── static/                 ← Static files (from movie-agent-demo)
│   ├── style.css
│   └── script.js
├── data/                   ← Movie data
│   └── movies.csv
└── movie_vectorstore/      ← Vector store (pre-built or built on first run)
    ├── index.faiss
    └── index.pkl
```

## Quick Reference

**Find your Hugging Face username:**
- Go to https://huggingface.co/settings
- Username is shown at the top

**Space repository URL:**
- Format: `https://huggingface.co/spaces/YOUR_USERNAME/SPACE_NAME`
- Example: `https://huggingface.co/spaces/ABZanganeh/movie-agent-service`

**Directory paths:**
- Service code: `/Users/admin/Desktop/projects/MovieOOP/movie-agent-service`
- Application (templates/static): `/Users/admin/Desktop/projects/MovieOOP/movie-agent-demo`
- Space repo: `/Users/admin/Desktop/projects/MovieOOP/hf-space`

## Resources

- [Hugging Face Spaces Documentation](https://huggingface.co/docs/hub/spaces)
- [Hugging Face Docker Spaces](https://huggingface.co/docs/hub/spaces-sdks-docker)
- [Flask Documentation](https://flask.palletsprojects.com/)
