#!/bin/bash
# Script to prepare and deploy Movie Agent Service to Hugging Face Spaces

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SPACES_DIR="$PROJECT_ROOT/spaces"

echo "🚀 Preparing deployment to Hugging Face Spaces..."

# Check if we're in the right directory
if [ ! -f "$PROJECT_ROOT/pyproject.toml" ]; then
    echo "Error: Must be run from movie-agent-service directory"
    exit 1
fi

# Get Space name from user
if [ -z "$1" ]; then
    echo "Usage: $0 <huggingface-username>/<space-name>"
    echo "Example: $0 myusername/movie-agent-service"
    exit 1
fi

SPACE_NAME="$1"
HF_REPO="https://huggingface.co/spaces/$SPACE_NAME"

echo "📦 Space: $SPACE_NAME"
echo "📍 Repository: $HF_REPO"

# Check if space repository exists locally
if [ -d "$SPACE_NAME" ]; then
    echo "⚠️  Directory $SPACE_NAME already exists"
    read -p "Remove and re-clone? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf "$SPACE_NAME"
    else
        echo "Aborted."
        exit 1
    fi
fi

# Clone the Space repository
echo "📥 Cloning Space repository..."
git clone "$HF_REPO" "$SPACE_NAME" || {
    echo "❌ Failed to clone repository. Make sure the Space exists and you have access."
    echo "Create it at: https://huggingface.co/spaces/new"
    exit 1
}

cd "$SPACE_NAME"

# Copy files
echo "📋 Copying files..."

# Copy source code
echo "  - Source code (src/)"
cp -r "$PROJECT_ROOT/src" ./

# Copy data directory
echo "  - Data files (data/)"
if [ -d "$PROJECT_ROOT/data" ]; then
    cp -r "$PROJECT_ROOT/data" ./
else
    echo "  ⚠️  Warning: data/ directory not found"
fi

# Copy deployment files from spaces/
echo "  - Deployment files"
cp "$SPACES_DIR/app.py" ./
cp "$SPACES_DIR/requirements.txt" ./
cp "$SPACES_DIR/README.md" ./
cp "$SPACES_DIR/.gitignore" ./

# Copy vector store if it exists
if [ -d "$PROJECT_ROOT/movie_vectorstore" ]; then
    echo "  - Vector store (movie_vectorstore/)"
    cp -r "$PROJECT_ROOT/movie_vectorstore" ./
    echo "  ✅ Pre-built vector store included"
else
    echo "  ⚠️  Vector store not found - will be built on first run"
fi

# Check git status
echo ""
echo "📊 Changes to commit:"
git status --short

echo ""
read -p "Commit and push to Hugging Face? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    git add .
    git commit -m "Deploy Movie Agent Service" || echo "No changes to commit"
    git push
    echo ""
    echo "✅ Deployment complete!"
    echo "🌐 View your Space at: $HF_REPO"
    echo ""
    echo "📝 Next steps:"
    echo "1. Go to Space Settings → Repository secrets"
    echo "2. Add your API keys:"
    echo "   - GROQ_API_KEY (or OPENAI_API_KEY)"
    echo "   - OPENAI_API_KEY (for embeddings)"
    echo "3. Wait for the Space to build (2-5 minutes)"
else
    echo "Files prepared in $SPACE_NAME/"
    echo "Review changes and commit manually:"
    echo "  cd $SPACE_NAME"
    echo "  git add ."
    echo "  git commit -m 'Deploy Movie Agent Service'"
    echo "  git push"
fi
