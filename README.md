# Movie Agent Service

An intelligent, agentic AI service for movie recommendations and discovery using RAG (Retrieval-Augmented Generation) and ReAct agent patterns.

## What It Does

The Movie Agent Service provides a conversational interface for:
- **Movie Discovery**: Natural language queries to find movies
- **Personalized Recommendations**: Context-aware suggestions based on user preferences
- **Poster Analysis**: Vision-based movie identification from poster images
- **Interactive Q&A**: Answer questions about movies, actors, directors, genres, and more

## Quick Start

### Prerequisites

- Python 3.10+
- OpenAI API key (for embeddings)
- Groq API key (for LLM) - optional, can use other providers

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd movie-agent-service

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export OPENAI_API_KEY="your-key-here"
export GROQ_API_KEY="your-key-here"  # Optional
```

### Running the Service

```bash
# Start the Flask server
python src/app.py

# Or run with development mode
FLASK_ENV=development python src/app.py
```

The service will be available at `http://localhost:5000`

### API Endpoints

See `local/CONTINUATION.md` for the complete public API specification.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    User Query (Text/Image)                    │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              MovieAgentService (Facade Layer)                │
│  - Entry point for UI                                        │
│  - Dependency injection                                      │
│  - Response formatting                                       │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              ToolCallingAgent (Orchestration)                │
│  - Single-step tool selection                                │
│  - LLM-based routing                                         │
│  - Output parsing                                            │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────┴───────────────────┐
        │                                       │
        ▼                                       ▼
┌──────────────────────┐          ┌──────────────────────┐
│   Search Tools       │          │   Vision Tools        │
│  - movie_search      │          │  - analyze_poster     │
│  - search_actor      │          │                       │
│  - search_director  │          └───────────┬───────────┘
│  - search_year       │                      │
└───────────┬──────────┘                      │
            │                                  │
            ▼                                  ▼
┌──────────────────────┐          ┌──────────────────────┐
│  MovieRetriever      │          │  BLIPVisionTool       │
│  (Protocol Impl)     │          │  (Vision Protocol)    │
└───────────┬──────────┘          └───────────┬───────────┘
            │                                 │
            ▼                                 │
┌──────────────────────┐                     │
│  MovieVectorStore     │◄────────────────────┘
│  (FAISS Storage)     │  (Title inference via retriever)
└──────────────────────┘
            │
            ▼
┌──────────────────────┐
│   Data Sources        │
│  - movies.csv         │
│  - FAISS index        │
│  - Embeddings (OpenAI)│
└──────────────────────┘
```

## Project Structure

```
movie-agent-service/
├── README.md              # This file - how to run, what it does
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
├── local/                 # Internal documents (gitignored)
│   ├── ARCHITECTURE.md   # System design (human-facing)
│   ├── DESIGN_DECISIONS.md # WHY decisions were made
│   ├── CONTINUATION.md   # LLM + human checkpoint
│   └── ...               # Other internal docs
└── src/                   # Source code
    ├── app.py            # Flask application (thin UI layer)
    └── ...               # Service implementation
```

## Documentation

Internal documentation is available in the `local/` directory (not tracked in git):
- **ARCHITECTURE.md**: High-level system design and component relationships
- **DESIGN_DECISIONS.md**: Rationale behind architectural choices
- **CONTINUATION.md**: Current state, rules, and next steps (checkpoint document)

## Development Status

This project is in active development. See `local/CONTINUATION.md` for current implementation status and next steps.

## License

[Add your license here]

