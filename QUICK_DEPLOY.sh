#!/bin/bash
# Quick deployment script for Hugging Face Spaces

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Movie Agent Service - Hugging Face Deployment${NC}"
echo ""

# Get Hugging Face username
read -p "Enter your Hugging Face username: " HF_USERNAME
SPACE_NAME="${HF_USERNAME}/movie-agent-service"

# Go to parent directory
cd /Users/admin/Desktop/projects/MovieOOP

# Remove existing clone if it exists
if [ -d "hf-space" ]; then
    echo -e "${YELLOW}⚠️  Removing existing hf-space directory...${NC}"
    rm -rf hf-space
fi

# Clone Space repository
echo -e "${GREEN}📥 Cloning Space repository...${NC}"
git clone https://huggingface.co/spaces/${SPACE_NAME} hf-space
cd hf-space

# Copy files
echo -e "${GREEN}📋 Copying files...${NC}"
cp ../movie-agent-service/Dockerfile ./
cp ../movie-agent-service/app.py ./
cp ../movie-agent-service/requirements.txt ./
cp -r ../movie-agent-service/src ./
cp -r ../movie-agent-service/templates ./
cp -r ../movie-agent-service/static ./
cp -r ../movie-agent-service/data ./
cp -r ../movie-agent-service/movie_vectorstore ./ 2>/dev/null || echo "  (Vector store will be built on first run)"

# Check status
echo -e "${GREEN}📊 Files copied. Current status:${NC}"
git status

echo ""
echo -e "${GREEN}✅ Ready to commit and push!${NC}"
echo ""
echo "Next steps:"
echo "  1. Review the files: git status"
echo "  2. Add files: git add ."
echo "  3. Commit: git commit -m 'Initial Flask deployment'"
echo "  4. Push: git push"
echo ""
echo "Then set API keys in Space Settings → Repository secrets:"
echo "  - GROQ_API_KEY"
echo "  - OPENAI_API_KEY"
