# Step-by-Step Deployment Guide

## Prerequisites

You should be at: `/Users/admin/Desktop/projects/MovieOOP/movie-agent-service`

## Step 1: Create Space on Hugging Face (if not done)

1. Go to https://huggingface.co/spaces
2. Click "Create new Space"
3. Fill in:
   - **Space name**: `movie-agent-service` (or your preferred name)
   - **SDK**: Select **Docker** (NOT Gradio!)
   - **Visibility**: Public or Private
4. Click "Create Space"

## Step 2: Clone Your Space Repository

**IMPORTANT**: Your service code is already in `movie-agent-service`, so we'll clone the Space repo with a different name to avoid conflicts.

Open a terminal and run these commands:

```bash
# Go to your projects directory (parent of movie-agent-service)
cd /Users/admin/Desktop/projects/MovieOOP

# Clone your Space repository with a different name (hf-space)
# Replace ABZanganeh with your actual Hugging Face username
git clone https://huggingface.co/spaces/ABZanganeh/movie-agent-service hf-space

# Go into the cloned Space directory
cd hf-space

# Check you're in the right place (should be empty or have README.md)
ls -la
```

**Your directory structure now:**
```
/Users/admin/Desktop/projects/MovieOOP/
├── movie-agent-service/    <-- Your service code (source)
└── hf-space/               <-- Your Space repo (destination)
```

## Step 3: Copy Files from Your Service to Space Repository

Now copy files from your `movie-agent-service` directory to the cloned Space repository:

```bash
# Make sure you're in the Space repository directory (hf-space)
cd /Users/admin/Desktop/projects/MovieOOP/hf-space

# Copy Dockerfile
cp ../movie-agent-service/Dockerfile ./

# Copy Flask app
cp ../movie-agent-service/app.py ./

# Copy requirements
cp ../movie-agent-service/requirements.txt ./

# Copy source code directory
cp -r ../movie-agent-service/src ./

# Copy templates (HTML files)
cp -r ../movie-agent-service/templates ./

# Copy static files (CSS, JS)
cp -r ../movie-agent-service/static ./

# Copy data directory (with movies.csv)
cp -r ../movie-agent-service/data ./

# Copy pre-built vector store (optional but recommended)
cp -r ../movie-agent-service/movie_vectorstore ./ 2>/dev/null || echo "Vector store will be built on first run"

# Check what you copied (you should see all these files/directories)
ls -la
```

You should now see:
- `Dockerfile`
- `app.py`
- `requirements.txt`
- `src/`
- `templates/`
- `static/`
- `data/`
- `movie_vectorstore/` (if it exists)

## Step 4: Commit and Push to Space

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

## Step 5: Set Environment Variables

1. Go to your Space page: https://huggingface.co/spaces/ABZanganeh/movie-agent-service
2. Click the **Settings** icon (gear) in the top right
3. Click **Repository secrets** in the left menu
4. Add these secrets (click "New secret" for each):

   **Secret 1:**
   - Name: `GROQ_API_KEY`
   - Value: (your Groq API key from https://console.groq.com)
   - Click "Save secret"

   **Secret 2:**
   - Name: `OPENAI_API_KEY`
   - Value: (your OpenAI API key from https://platform.openai.com)
   - Click "Save secret"

5. Go back to the **App** tab

## Step 6: Wait for Build

- The Space will automatically start building (check the **Logs** tab)
- First build takes 5-10 minutes
- You'll see progress in the logs

## Step 7: Test Your Deployment

Once the build completes:
1. Go to the **App** tab
2. Your Flask app should be running!
3. Test the chat and poster upload features

## Troubleshooting

### If you already cloned the Space repo:
```bash
# If you already cloned it (maybe with the same name), remove it first
cd /Users/admin/Desktop/projects/MovieOOP
rm -rf hf-space  # Remove if exists

# Then clone again
git clone https://huggingface.co/spaces/ABZanganeh/movie-agent-service hf-space
cd hf-space
```

### Alternative: Clone to your home directory (if you prefer):
```bash
cd ~
git clone https://huggingface.co/spaces/ABZanganeh/movie-agent-service
cd movie-agent-service
# Then copy from:
# /Users/admin/Desktop/projects/MovieOOP/movie-agent-service
```

### To check your Hugging Face username:
- Go to https://huggingface.co/settings
- Your username is shown at the top

### Verify files are correct:
```bash
# In your Space repository directory
ls -la app.py Dockerfile requirements.txt  # Should exist
ls -la src/ templates/ static/ data/       # Should exist
```
