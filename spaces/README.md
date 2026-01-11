---
title: Movie Agent Service
emoji: 🎬
colorFrom: blue
colorTo: purple
sdk: gradio
sdk_version: 4.0.0
app_file: app.py
pinned: false
license: mit
---

# 🎬 Movie Agent Service

An AI-powered movie discovery and analysis service using RAG (Retrieval-Augmented Generation) and tool-calling agent architecture.

## Features

- 🔍 **Semantic Movie Search**: Find movies using natural language queries
- 📊 **Movie Statistics**: Get top-rated movies, genre distributions, and comparisons
- 🎨 **Poster Analysis**: Upload movie posters for visual analysis and identification
- 💬 **Conversational Interface**: Chat naturally about movies with context awareness
- 🧠 **Memory**: Maintains conversation context across multiple interactions

## Usage

### Chat Interface

Ask questions about movies in natural language:
- "Find sci-fi movies from the 2000s"
- "What are the top rated action movies?"
- "Show me movies similar to The Matrix"
- "Compare The Dark Knight and Inception"

### Poster Analysis

Upload a movie poster image to:
- Analyze visual elements (colors, mood, themes)
- Identify potential genres
- Generate descriptive captions
- Attempt movie identification

## Configuration

### Required Environment Variables

Set these in your Space settings (Settings → Repository secrets):

1. **LLM API Key** (choose one):
   - `GROQ_API_KEY` - For Groq LLM (recommended, faster)
   - `OPENAI_API_KEY` - For OpenAI LLM

2. **Embeddings API Key**:
   - `OPENAI_API_KEY` - Required for vector embeddings (if using OpenAI embeddings)

### Optional Environment Variables

- `LLM_PROVIDER`: "groq" or "openai" (default: "groq")
- `LLM_MODEL`: Model name (default: "llama-3.1-8b-instant" for Groq)
- `ENABLE_VISION`: "true" or "false" (default: "true")
- `ENABLE_MEMORY`: "true" or "false" (default: "true")
- `DEVICE`: "auto", "cpu", "cuda", "mps" (default: "auto")
- `FORCE_CPU`: "true" or "false" (default: "false")

## Architecture

- **RAG System**: FAISS vector store for semantic search
- **Agent Framework**: LangChain with tool-calling capabilities
- **Vision**: BLIP model for poster analysis (optional)
- **LLM**: Groq or OpenAI for natural language understanding

## Technical Details

- Built with Python and Gradio
- Uses LangChain for agent orchestration
- FAISS for efficient vector similarity search
- Supports multiple LLM providers (Groq, OpenAI)
- Hardware-aware (GPU acceleration when available)

## License

MIT License

## Author

Alireza Barzin Zanganeh

---

For more information, see the [project repository](https://github.com/abzanganeh/movie-agent-service).
