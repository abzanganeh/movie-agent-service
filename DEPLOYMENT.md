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

# Note: Vector store and binary files are NOT copied (too large for git)
# Vector store will be built automatically on first run (takes a few minutes)
# Create .gitignore to exclude large/binary files
echo -e "movie_vectorstore/\n*.png\n__pycache__/\n*.pyc" > .gitignore
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

**Authentication**: When prompted for credentials:
- **Username**: Your Hugging Face username
- **Password**: Your Hugging Face access token (not your account password!)

**To create an access token:**
1. Go to https://huggingface.co/settings/tokens
2. Click "New token"
3. Name it (e.g., "movie-agent-deployment")
4. Select "Write" permissions
5. Copy the token (starts with `hf_...`)
6. Use this token as the password when pushing

**Tip**: Configure git to remember credentials:
```bash
git config --global credential.helper osxkeychain
```
Then you'll only need to enter credentials once.

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

- **First run**: Vector store builds automatically (takes 5-10 minutes)
- **Large files**: Vector store files are too large (>10MB) for git, so they're not included
- **Automatic**: The app will build the vector store from `data/movies.csv` on first startup
- **Check logs**: Vector store build progress is visible in logs
- **Note**: If you need to include it, use Git LFS (see troubleshooting below)

### Port Issues

- **Automatic**: Hugging Face Spaces sets `PORT` environment variable automatically
- **Don't hardcode**: App reads `PORT` from environment (default: 7860)

### Large Files Error (>10MB) or Binary Files Error

If you get errors about large files or binary files:

**Solution (Recommended)**: Exclude large/binary files
- Vector store: Will be built automatically on first run
- Binary files (PNG, etc.): Not needed for deployment
- Python cache: Should never be committed

Create/update `.gitignore`:
```bash
echo -e "movie_vectorstore/\n*.png\n__pycache__/\n*.pyc" > .gitignore
git rm --cached -r movie_vectorstore/ data/posters/ src/**/__pycache__/ 2>/dev/null
git add .gitignore
git commit --amend --no-edit
git push --force
```

**Alternative**: Use Git LFS (if you must include large files)
```bash
# Install Git LFS
brew install git-lfs  # macOS
# or: apt-get install git-lfs  # Linux

# Initialize in your repo
cd hf-space
git lfs install
git lfs track "movie_vectorstore/*.faiss"
git lfs track "movie_vectorstore/*.pkl"
git add .gitattributes
git commit -m "Add Git LFS tracking for vector store"
git push
```

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
└── data/                   ← Movie data
    └── movies.csv

Note: `movie_vectorstore/` is NOT included (too large for git). It will be built automatically on first run.
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
