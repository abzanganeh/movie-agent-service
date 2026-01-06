# Movie Agent Service

An intelligent, agentic AI service for movie recommendations and discovery using RAG (Retrieval-Augmented Generation) and tool-calling agent patterns.

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

# Set up configuration
# Option 1: Copy .env.example to .env and fill in your keys
cp .env.example .env
# Then edit .env with your actual API keys

# Option 2: Set environment variables directly
export OPENAI_API_KEY="your-key-here"
export GROQ_API_KEY="your-key-here"
```

### Using the Public API

The public API is accessed through `MovieAgentApp`, which is the single stable entry point:

```python
from movie_agent.app import MovieAgentApp
from movie_agent.config import MovieAgentConfig

# Create configuration
config = MovieAgentConfig(
    movies_csv_path="data/movies.csv",
    enable_vision=True,
)

# Create and initialize app
app = MovieAgentApp(config)
app.initialize()

# Use the app
response = app.chat("Find sci-fi movies like Inception")
print(response.answer)

# Analyze poster
poster_response = app.analyze_poster("path/to/poster.png")
print(poster_response.title)
```

### Running the Demo

#### Interactive CLI Demo

```bash
# Run the interactive CLI demo
PYTHONPATH=src python demo/cli_demo.py
```

The CLI demo provides an interactive loop where you can:
- Ask movie questions (e.g., "Recommend sci-fi movies like Inception")
- Analyze movie posters (e.g., "Analyze poster at path data/posters/test_poster01.png")
- Generate quizzes, compare movies, search by actor/director/year
- Type `quit` or `exit` to end the session

**Logging**: All interactions are automatically logged to `logs/cli_demo_TIMESTAMP.log` in JSON format. You can:
- Specify a custom log file: `python demo/cli_demo.py --log-file my_session.log`
- Disable logging: `python demo/cli_demo.py --no-log`
- Set log file via environment variable: `export LOG_FILE=my_session.log`

#### Evaluation Scripts

```bash
# Run production evaluation with real LLM and tools
PYTHONPATH=src python -m evaluation.run_real

# Run dummy evaluation with mock tools (for testing)
PYTHONPATH=src python -m evaluation.run
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    User Query (Text/Image)                    │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              MovieAgentApp (Public API)                      │
│  - Single stable entry point                                 │
│  - Encapsulates all internal wiring                          │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              MovieAgentService (Internal Facade)             │
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
├── demo/                  # Demo scripts
│   └── cli_demo.py       # Interactive CLI demo
├── evaluation/           # Evaluation scripts
│   ├── run_real.py       # Production evaluation
│   └── run.py            # Dummy evaluation
└── src/                   # Source code
    └── movie_agent/      # Core service implementation
        ├── agent/        # Agent orchestration
        ├── tools/        # Tool implementations
        └── ...           # Other modules
```

## Documentation

Internal documentation is available in the `local/` directory (not tracked in git):
- **ARCHITECTURE.md**: High-level system design and component relationships
- **DESIGN_DECISIONS.md**: Rationale behind architectural choices
- **CONTINUATION.md**: Current state, rules, and next steps (checkpoint document)

## Development Status

This project is in active development. See `local/CONTINUATION.md` for current implementation status and next steps.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

