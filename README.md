# Movie Agent Service

An intelligent agentic AI service for movie recommendations and discovery using RAG and tool-calling patterns.

**Author:** Alireza Barzin Zanganeh  
**Website:** [zanganehai.com](https://www.zanganehai.com/about)

## Overview

This service provides a conversational interface for discovering movies, getting recommendations, analyzing posters, and answering questions about films, actors, directors, and genres.

## Quick Start

### Prerequisites

- Python 3.10+
- OpenAI API key (required for embeddings)
- Groq or OpenAI API key (for LLM)

### Installation

```bash
git clone <repository-url>
cd movie-agent-service
pip install -r requirements.txt

# Set up configuration
cp .env.example .env
# Edit .env with your API keys
```

### Basic Usage

The service is accessed through `MovieAgentApp`, which is the main entry point:

```python
from movie_agent.app import MovieAgentApp
from movie_agent.config import MovieAgentConfig

config = MovieAgentConfig(
    movies_csv_path="data/movies.csv",
    enable_vision=True,
)

app = MovieAgentApp(config)
app.initialize()

response = app.chat("Find sci-fi movies like Inception")
print(response.answer)

poster_response = app.analyze_poster("path/to/poster.png")
print(poster_response.title)
```

### Demo

Run the interactive CLI demo:

```bash
PYTHONPATH=src python demo/cli_demo.py
```

This provides an interactive session where you can ask questions, analyze posters, take quizzes, and compare movies. Type `quit` or `exit` to end.

Interactions are logged to `logs/cli_demo_TIMESTAMP.log` in JSON format. You can customize logging with:
- `--log-file` to specify a custom log file
- `--no-log` to disable logging
- `LOG_FILE` environment variable

## Architecture

The service follows a layered architecture with clear separation of concerns:

- **MovieAgentApp**: Public API facade (stable interface)
- **MovieAgentService**: Internal service layer (dependency injection, response formatting)
- **ToolCallingAgent**: Orchestration layer (tool selection and execution)
- **Tools**: Specialized tools for search, statistics, comparison, quizzes, and vision
- **Vector Store**: FAISS-based storage for semantic search

The codebase is structured with OOP principles:
- Single Responsibility: Each class has one clear purpose
- Dependency Inversion: Dependencies are injected, not hardcoded
- Factory Pattern: Tools and components are created via factories
- Strategy Pattern: Different question generators for quiz types

## Project Structure

```
movie-agent-service/
├── src/movie_agent/          # Core service code
│   ├── app.py                # Public API facade
│   ├── service.py            # Service layer
│   ├── agent/                # Agent orchestration
│   ├── tools/                # Tool implementations
│   ├── memory/               # Session and quiz state
│   └── ...
├── demo/                     # Demo scripts
├── evaluation/               # Evaluation scripts
├── data/                     # Movie dataset
└── local/                    # Internal documentation (gitignored)
```

## Development

Internal documentation and design decisions are in the `local/` directory, which is not tracked in git.

## License

MIT License - see LICENSE file for details.
