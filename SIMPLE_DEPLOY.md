# Simple Deployment Guide - Copy & Paste Commands

## Current Situation

You have:
- **Your service code**: `/Users/admin/Desktop/projects/MovieOOP/movie-agent-service`
- **Your Space repository**: Will be cloned to a new directory

## Step 1: Open Terminal

Open Terminal on your Mac.

## Step 2: Clone Your Space Repository

Copy and paste these commands ONE BY ONE:

```bash
# Go to your projects directory
cd /Users/admin/Desktop/projects/MovieOOP

# Clone your Space (replace ABZanganeh with YOUR username)
git clone https://huggingface.co/spaces/ABZanganeh/movie-agent-service hf-space

# Go into the cloned directory
cd hf-space
```

**What just happened:**
- Created a new folder: `hf-space` 
- This is your Hugging Face Space repository
- Location: `/Users/admin/Desktop/projects/MovieOOP/hf-space`

## Step 3: Copy Your Flask App Files

Still in the `hf-space` directory, copy and paste these commands:

```bash
# Copy Dockerfile
cp ../movie-agent-service/Dockerfile ./

# Copy Flask app
cp ../movie-agent-service/app.py ./

# Copy requirements
cp ../movie-agent-service/requirements.txt ./

# Copy source code
cp -r ../movie-agent-service/src ./

# Copy templates
cp -r ../movie-agent-service/templates ./

# Copy static files
cp -r ../movie-agent-service/static ./

# Copy data
cp -r ../movie-agent-service/data ./

# Copy vector store (optional)
cp -r ../movie-agent-service/movie_vectorstore ./ 2>/dev/null || echo "OK - will build on first run"
```

**What this does:**
- Copies files FROM: `movie-agent-service/` (your source code)
- Copies files TO: `hf-space/` (your Space repo, where you are now)

## Step 4: Check Files Are There

```bash
# List files to verify
ls -la
```

You should see:
- `Dockerfile`
- `app.py`
- `requirements.txt`
- `src/` (folder)
- `templates/` (folder)
- `static/` (folder)
- `data/` (folder)

## Step 5: Commit and Push

```bash
# Check what will be committed
git status

# Add all files
git add .

# Commit
git commit -m "Initial Flask deployment"

# Push to Hugging Face
git push
```

## Step 6: Set API Keys

1. Go to: https://huggingface.co/spaces/ABZanganeh/movie-agent-service
2. Click **Settings** (gear icon)
3. Click **Repository secrets**
4. Add:
   - Name: `GROQ_API_KEY`, Value: (your key)
   - Name: `OPENAI_API_KEY`, Value: (your key)
5. Go to **App** tab and wait for build

---

## Quick Reference: Where Everything Is

```
/Users/admin/Desktop/projects/MovieOOP/
│
├── movie-agent-service/     ← Your SOURCE code (don't modify)
│   ├── Dockerfile
│   ├── app.py
│   ├── src/
│   ├── templates/
│   └── ...
│
└── hf-space/                ← Your Space repo (THIS is what you push)
    ├── Dockerfile           ← Copied from above
    ├── app.py               ← Copied from above
    ├── src/                 ← Copied from above
    └── ...
```

**You work in**: `hf-space/` directory
**You copy from**: `../movie-agent-service/` (one level up)

---

## Need Your Hugging Face Username?

1. Go to https://huggingface.co/settings
2. Your username is at the top
3. Replace `ABZanganeh` in the commands above with YOUR username
