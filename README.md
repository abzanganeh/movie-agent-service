# Movie Agent Service

An intelligent, agentic AI service for movie recommendations and discovery using RAG (Retrieval-Augmented Generation) and tool-calling agent patterns.

**Author:** Alireza Barzin Zanganeh  
**Website:** [zanganehai.com](https://www.zanganehai.com/about)

## Overview

The Movie Agent Service provides a conversational interface for movie discovery, recommendations, and analysis. It uses advanced AI techniques including:

- **RAG (Retrieval-Augmented Generation)**: Semantic search over movie database
- **Tool-Calling Agents**: LLM-powered decision making with structured tools
- **Computer Vision**: Movie poster analysis and identification
- **Session Management**: Context-aware conversations with memory

## Features

- **Natural Language Movie Search**: Find movies using conversational queries
- **Personalized Recommendations**: Context-aware suggestions based on user preferences
- **Poster Analysis**: Vision-based movie identification from poster images
- **Interactive Quizzes**: Movie trivia with one-question-at-a-time format
- **Movie Comparisons**: Compare movies across multiple dimensions
- **Actor/Director Search**: Find movies by cast and crew
- **Year-based Filtering**: Search movies by release year or decade

## Quick Start

### Prerequisites

- Python 3.10 or higher
- OpenAI API key (required for embeddings)
- LLM API key (Groq recommended, or OpenAI)

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd movie-agent-service

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
export OPENAI_API_KEY="your-openai-key"
export GROQ_API_KEY="your-groq-key"  # Optional, can use OpenAI for LLM
export LLM_PROVIDER="groq"  # or "openai"
export LLM_MODEL="llama-3.1-8b-instant"  # Groq model, or "gpt-4" for OpenAI
```

### Using the Public API

The service is accessed through `MovieAgentApp`, which provides a stable public interface:

```python
from movie_agent.app import MovieAgentApp
from movie_agent.config_loader import load_config_from_env

# Load configuration from environment variables
config = load_config_from_env()

# Create and initialize app
app = MovieAgentApp(config)
app.initialize()

# Chat with the agent
response = app.chat("Find sci-fi movies like Inception", session_id="user123")
print(response.answer)
print(response.movies)

# Analyze a movie poster
poster_response = app.analyze_poster("path/to/poster.png", session_id="user123")
print(f"Title: {poster_response.title}")
print(f"Mood: {poster_response.mood}")
print(f"Genres: {poster_response.inferred_genres}")
```

### Running the CLI Demo

```bash
# Run interactive CLI demo
PYTHONPATH=src python demo/cli_demo.py
```

The CLI demo provides an interactive session where you can:
- Ask movie questions
- Analyze movie posters
- Generate quizzes
- Compare movies
- Search by actor, director, or year

## Architecture

The service follows a clean architecture with clear separation of concerns:

```
┌─────────────────────────────────────────┐
│         MovieAgentApp (Public API)      │
│         Single stable entry point       │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│      MovieAgentService (Facade)         │
│      - Intent Detection                 │
│      - Memory Management                │
│      - State Management                 │
│      - Response Formatting              │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│    ToolCallingAgent (Orchestration)    │
│    - Single-step tool selection         │
│    - LLM-based routing                  │
└──────────────────┬──────────────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
        ▼                     ▼
┌──────────────┐    ┌──────────────────┐
│ Search Tools │    │  Vision Tools    │
│ - movie_search│    │  - analyze_poster │
│ - search_actor│    └──────────────────┘
│ - search_year │
│ - generate_quiz│
└──────────────┘
```

## Project Structure

```
movie-agent-service/
├── README.md                 # This file
├── requirements.txt          # Python dependencies
├── src/                      # Source code
│   └── movie_agent/         # Core package
│       ├── app.py           # Public API (MovieAgentApp)
│       ├── service.py        # Service facade
│       ├── agent/           # Agent orchestration
│       ├── tools/           # Tool implementations
│       ├── memory/          # Session memory management
│       ├── orchestration/   # Workflow orchestration
│       ├── context/         # Session context
│       └── intent/         # Intent detection
├── demo/                    # Demo scripts
├── tests/                   # Unit tests
└── local/                   # Internal documentation
```

## Configuration

Configuration is managed through environment variables. See `CONFIGURATION.md` for complete details.

**Required:**
- `OPENAI_API_KEY`: OpenAI API key for embeddings

**Optional:**
- `GROQ_API_KEY`: Groq API key for LLM (if using Groq)
- `LLM_PROVIDER`: "groq" or "openai" (default: "groq")
- `LLM_MODEL`: Model name (default: "llama-3.1-8b-instant")
- `MOVIE_DATA_CSV_PATH`: Path to movies CSV (default: "data/movies.csv")
- `VECTOR_STORE_PATH`: Path to FAISS index (default: auto-generated)
- `ENABLE_VISION`: Enable poster analysis (default: "false")
- `VERBOSE`: Enable verbose logging (default: "false")

## API Reference

### MovieAgentApp

Main entry point for the service.

#### Methods

**`initialize()`**
- Initializes the service with all dependencies
- Must be called before using other methods

**`chat(query: str, session_id: str = "default") -> ChatResponse`**
- Send a chat query to the agent
- Returns structured response with answer, movies, and metadata

**`analyze_poster(image_path: str, session_id: str = "default") -> PosterAnalysisResponse`**
- Analyze a movie poster image
- Returns title, mood, genres, and confidence score

### ChatResponse

Response object from chat queries.

**Fields:**
- `answer: str` - Agent's response text
- `movies: List[str]` - List of movie titles found
- `tools_used: List[str]` - Tools invoked by the agent
- `llm_latency_ms: int` - LLM processing time
- `tool_latency_ms: int` - Tool execution time
- `latency_ms: int` - Total response time
- `reasoning_type: str` - Type of reasoning used
- `confidence: float` - Confidence score (0.0-1.0)
- `quiz_data: Optional[Dict]` - Quiz data if quiz is active

### PosterAnalysisResponse

Response object from poster analysis.

**Fields:**
- `caption: str` - Visual description of the poster
- `title: Optional[str]` - Identified movie title
- `mood: str` - Synthesized mood (e.g., "Dramatic", "Comedic")
- `confidence: float` - Confidence score (0.0-1.0)
- `inferred_genres: List[str]` - Genres inferred from visual analysis

## Testing

Run the test suite (requires dependencies to be installed):

```bash
# Install test dependencies
pip install -r requirements.txt

# Run all tests
PYTHONPATH=src python -m pytest tests/ -v

# Or using unittest
PYTHONPATH=src python -m unittest discover tests -v

# Run specific test file
PYTHONPATH=src python -m unittest tests.test_service -v
```

**Note:** Tests require all dependencies from `requirements.txt` to be installed, including LangChain packages and pytest.

## Development

### Code Organization

The codebase follows Object-Oriented Programming principles:

- **Single Responsibility**: Each class has one clear purpose
- **Encapsulation**: Internal state is protected
- **Dependency Injection**: Dependencies are injected, not created
- **Separation of Concerns**: Clear boundaries between layers

### Adding New Tools

1. Create tool class in `src/movie_agent/tools/`
2. Implement `BaseTool` interface
3. Add tool to `MovieAgentService.warmup()`
4. Update agent prompt if needed

### Adding New Features

1. Follow existing patterns in service layer
2. Maintain separation of concerns
3. Add appropriate tests
4. Update documentation

## Limitations

This is a demo version using a limited movie dataset (CSV). Results may not include all movies, and some queries may return fewer results compared to a full production database.

## License

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.

## Author

**Alireza Barzin Zanganeh**  
Software Engineer | ML Engineer | GenAI Practitioner

For more information, visit [zanganehai.com](https://www.zanganehai.com/about)
