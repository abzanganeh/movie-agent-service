# Deploying to Hugging Face Spaces

This guide explains how to deploy the Movie Agent Service to Hugging Face Spaces.

## Prerequisites

1. **Hugging Face Account**: Create an account at [huggingface.co](https://huggingface.co)
2. **Git Repository**: Your code should be in a Git repository
3. **API Keys**: Get API keys for:
   - Groq API: [console.groq.com](https://console.groq.com) (recommended)
   - OpenAI API: [platform.openai.com](https://platform.openai.com) (alternative)

## Deployment Steps

### Step 1: Prepare Your Repository

1. **Copy files to a deployment directory**:
   ```bash
   cd movie-agent-service
   mkdir -p spaces
   # The spaces/ directory should contain:
   # - app.py (Gradio app)
   # - requirements.txt
   # - README.md
   ```

2. **Ensure data files are accessible**:
   - The `data/movies.csv` file must be in the repository
   - The `movie_vectorstore/` directory should be built (or will be built on first run)

### Step 2: Create a Hugging Face Space

1. Go to [Hugging Face Spaces](https://huggingface.co/spaces)
2. Click **"Create new Space"**
3. Fill in the form:
   - **Space name**: `movie-agent-service` (or your preferred name)
   - **SDK**: Select **Gradio**
   - **Visibility**: Choose Public or Private
   - Click **"Create Space"**

### Step 3: Upload Your Code

#### Option A: Using Git (Recommended)

1. **Clone your Space repository**:
   ```bash
   git clone https://huggingface.co/spaces/YOUR_USERNAME/YOUR_SPACE_NAME
   cd YOUR_SPACE_NAME
   ```

2. **Copy necessary files**:
   ```bash
   # Copy the service source code
   cp -r ../movie-agent-service/src ./src
   
   # Copy data directory
   cp -r ../movie-agent-service/data ./data
   
   # Copy spaces deployment files
   cp ../movie-agent-service/spaces/app.py ./
   cp ../movie-agent-service/spaces/requirements.txt ./
   cp ../movie-agent-service/spaces/README.md ./
   cp ../movie-agent-service/spaces/.gitignore ./
   ```

3. **Commit and push**:
   ```bash
   git add .
   git commit -m "Initial deployment"
   git push
   ```

#### Option B: Using Web Interface

1. Go to your Space page
2. Click **"Files and versions"** tab
3. Click **"Add file"** → **"Upload files"**
4. Upload:
   - `app.py`
   - `requirements.txt`
   - `README.md`
   - `src/` directory (entire folder)
   - `data/` directory (entire folder)

### Step 4: Configure Environment Variables

1. Go to your Space settings
2. Navigate to **"Repository secrets"** or **"Variables"** section
3. Add the following secrets:

   **Required:**
   - `GROQ_API_KEY`: Your Groq API key (or use `OPENAI_API_KEY` instead)
   - `OPENAI_API_KEY`: Your OpenAI API key (for embeddings, required)

   **Optional:**
   - `LLM_PROVIDER`: `"groq"` or `"openai"` (default: `"groq"`)
   - `LLM_MODEL`: Model name (default: `"llama-3.1-8b-instant"`)
   - `ENABLE_VISION`: `"true"` or `"false"` (default: `"true"`)
   - `ENABLE_MEMORY`: `"true"` or `"false"` (default: `"true"`)

### Step 5: Build Vector Store (Optional)

The vector store will be built automatically on first run, but if you want to pre-build it:

1. **Build locally**:
   ```bash
   python -c "
   from movie_agent.app import MovieAgentApp
   from movie_agent.config import MovieAgentConfig
   config = MovieAgentConfig()
   app = MovieAgentApp(config)
   app.initialize()
   "
   ```

2. **Upload the built vector store**:
   ```bash
   # In your Space repository
   git add movie_vectorstore/
   git commit -m "Add pre-built vector store"
   git push
   ```

### Step 6: Deploy and Test

1. **Automatic Deployment**: Hugging Face Spaces automatically builds and deploys when you push code
2. **Monitor Logs**: Check the "Logs" tab in your Space for any errors
3. **Test the Interface**: Once deployed, test both chat and poster analysis features

## Troubleshooting

### Common Issues

#### 1. **"Module not found" errors**
   - Ensure `requirements.txt` includes all dependencies
   - Check that `src/` directory is properly uploaded

#### 2. **"API key not found" errors**
   - Verify environment variables are set in Space settings
   - Check that variable names match exactly (case-sensitive)

#### 3. **"Vector store not found" errors**
   - The vector store will be built on first run (takes a few minutes)
   - Ensure `data/movies.csv` is present
   - Check logs for build errors

#### 4. **"Out of memory" errors**
   - Spaces have limited memory (16GB free tier)
   - Set `ENABLE_VISION=false` if poster analysis isn't needed
   - Use smaller models or CPU-only mode: `FORCE_CPU=true`

#### 5. **Slow startup**
   - First startup builds the vector store (can take 5-10 minutes)
   - Subsequent startups are faster
   - Pre-build and upload the vector store to speed up deployment

### Performance Optimization

1. **Use Groq instead of OpenAI**:
   - Much faster inference
   - More generous rate limits
   - Set `LLM_PROVIDER=groq`

2. **Disable vision if not needed**:
   - Saves memory and startup time
   - Set `ENABLE_VISION=false`

3. **Pre-build vector store**:
   - Upload `movie_vectorstore/` directory
   - Avoids build time on first run

4. **Use CPU-only mode**:
   - Set `FORCE_CPU=true` and `DEVICE=cpu`
   - Reduces memory usage

## Updating Your Deployment

1. **Make changes locally**
2. **Push to your Space repository**:
   ```bash
   cd YOUR_SPACE_NAME
   git add .
   git commit -m "Update: description of changes"
   git push
   ```
3. **Space will automatically rebuild** (takes 2-5 minutes)

## Customization

### Modify the Gradio Interface

Edit `app.py` to customize:
- UI layout and themes
- Input/output formats
- Additional features or tabs

### Add Custom Models

1. Upload model files to your Space
2. Update `app.py` to load from local paths
3. Modify `MovieAgentConfig` as needed

## Advanced: Using Docker

For more control, you can use a Docker deployment:

1. Create `Dockerfile` in your Space
2. Set SDK to "Docker" instead of "Gradio"
3. Build and deploy

See [Hugging Face Docker Spaces docs](https://huggingface.co/docs/hub/spaces-sdks-docker) for details.

## Resources

- [Hugging Face Spaces Documentation](https://huggingface.co/docs/hub/spaces)
- [Gradio Documentation](https://www.gradio.app/docs/)
- [Project Repository](https://github.com/abzanganeh/movie-agent-service)

## Support

For issues or questions:
1. Check the logs in your Space
2. Review the [troubleshooting section](#troubleshooting)
3. Open an issue on the GitHub repository
