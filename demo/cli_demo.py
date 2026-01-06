#!/usr/bin/env python3
"""
Interactive CLI demo for Movie Agent Service.

Provides a simple command-line interface to interact with the movie agent.
Demonstrates the agent's capabilities in a user-friendly way.

Logging:
    Interactions are logged to a file. Set LOG_FILE environment variable
    to specify the log file path, or use --log-file command-line argument.
    Default: logs/cli_demo_YYYYMMDD_HHMMSS.log
"""
import os
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Public API import - this is the only import clients should use
from movie_agent.app import MovieAgentApp
from movie_agent.config import MovieAgentConfig
from movie_agent.interaction import IntentRouter, IntentType

# Load environment variables
load_dotenv()


class InteractionLogger:
    """Logs CLI interactions to a file."""
    
    def __init__(self, log_file: str):
        """Initialize logger with log file path."""
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        self.session_start = datetime.now()
        
        # Write session header
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(f"\n{'='*80}\n")
            f.write(f"Session started: {self.session_start.isoformat()}\n")
            f.write(f"{'='*80}\n\n")
    
    def log_query(self, query: str, query_type: str = "chat"):
        """Log a user query."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "type": query_type,
            "query": query,
        }
        self._write_entry(entry)
    
    def log_response(self, response, query: str, query_type: str = "chat"):
        """Log an agent response."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "type": f"{query_type}_response",
            "query": query,
            "answer": response.answer if hasattr(response, 'answer') else str(response),
            "movies": response.movies if hasattr(response, 'movies') else [],
            "tools_used": response.tools_used if hasattr(response, 'tools_used') else [],
            "llm_latency_ms": response.llm_latency_ms if hasattr(response, 'llm_latency_ms') else None,
            "tool_latency_ms": response.tool_latency_ms if hasattr(response, 'tool_latency_ms') else None,
            "latency_ms": response.latency_ms if hasattr(response, 'latency_ms') else None,
        }
        
        # Add resolution metadata if available
        if hasattr(response, 'resolution_metadata') and response.resolution_metadata:
            entry["resolution_metadata"] = response.resolution_metadata
        
        # For poster analysis responses
        if hasattr(response, 'title'):
            entry["title"] = response.title
        if hasattr(response, 'inferred_genres'):
            entry["inferred_genres"] = response.inferred_genres
        if hasattr(response, 'mood'):
            entry["mood"] = response.mood
        if hasattr(response, 'confidence'):
            entry["confidence"] = response.confidence
        
        self._write_entry(entry)
    
    def log_error(self, query: str, error: Exception, query_type: str = "chat"):
        """Log an error."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "error",
            "query": query,
            "error": str(error),
            "error_type": type(error).__name__,
        }
        self._write_entry(entry)
    
    def _write_entry(self, entry: dict):
        """Write a log entry to file."""
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    
    def close(self):
        """Close the log session."""
        session_end = datetime.now()
        duration = (session_end - self.session_start).total_seconds()
        
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(f"\n{'='*80}\n")
            f.write(f"Session ended: {session_end.isoformat()}\n")
            f.write(f"Duration: {duration:.2f} seconds\n")
            f.write(f"{'='*80}\n\n")


def cleanup_old_logs():
    """Clean up old log files before starting new session."""
    from movie_agent.utils import cleanup_logs
    
    logs_dir = Path(__file__).parent.parent / "logs"
    # Keep max 10 files, delete files older than 7 days
    cleanup_logs(str(logs_dir), max_files=10, max_age_days=7, pattern="cli_demo_*.log")


def get_log_file_path(log_file_arg: str = None) -> str:
    """Get log file path from argument or environment variable."""
    if log_file_arg:
        return log_file_arg
    
    log_file = os.getenv("LOG_FILE")
    if log_file:
        return log_file
    
    # Default: create timestamped log file in logs/ directory
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return str(logs_dir / f"cli_demo_{timestamp}.log")


def print_banner(log_file: str = None):
    """Print welcome banner."""
    print("\n" + "=" * 60)
    print("  Movie Agent Service - Interactive CLI Demo")
    print("=" * 60)
    print("\nAsk me about movies! I can:")
    print("  • Recommend movies by genre, year, or description")
    print("  • Analyze movie posters")
    print("  • Generate movie quizzes")
    print("  • Compare movies")
    print("  • Search by actor, director, or year")
    print("\nType 'quit' or 'exit' to end the session.")
    if log_file:
        print(f"\n📝 Logging interactions to: {log_file}")
    print("-" * 60 + "\n")


def print_response(response, query):
    """Print formatted response."""
    print(f"\n📽️  Query: {query}")
    print(f"💬 Answer: {response.answer}")
    
    if response.movies:
        print(f"🎬 Movies: {', '.join(response.movies)}")
    
    if response.tools_used:
        print(f"🔧 Tools used: {', '.join(response.tools_used)}")
    
    if response.llm_latency_ms is not None:
        print(f"⚡ Latency: {response.latency_ms}ms total "
              f"(LLM: {response.llm_latency_ms}ms, "
              f"Tools: {response.tool_latency_ms or 0}ms)")
    
    print("-" * 60)


def setup_app():
    """Set up and initialize the movie agent app."""
    print("🚀 Initializing Movie Agent Service...")
    
    # Load configuration from environment (with validation)
    # Uses professional config loader with helpful error messages
    from movie_agent.config_loader import load_config_from_env
    
    config = load_config_from_env()
    
    # Override specific settings for CLI demo
    config.warmup_on_start = False
    config.enable_vision = True
    config.enable_memory = True  # Enable conversation memory for follow-up questions
    config.memory_max_turns = 10  # Keep last 10 conversation turns
    
    # Create app (handles all internal wiring)
    app = MovieAgentApp(config)
    
    # Initialize (builds vector store, creates tools, warms up)
    print("🔥 Initializing agent...")
    app.initialize()
    print("✅ Ready!\n")
    
    return app


def handle_poster_query(app, query, session_id: str, logger: InteractionLogger = None):
    """Handle poster analysis queries."""
    # Extract poster path from query
    if "poster" in query.lower() and "path" in query.lower():
        # Try to extract path
        parts = query.split()
        path_idx = None
        for i, part in enumerate(parts):
            if part == "path" and i + 1 < len(parts):
                path_idx = i + 1
                break
        
        if path_idx and path_idx < len(parts):
            poster_path = parts[path_idx]
            try:
                if logger:
                    logger.log_query(query, query_type="poster")
                
                # Pass session_id for memory storage (same as Flask app)
                response = app.analyze_poster(poster_path, session_id=session_id)
                
                print(f"\n📽️  Query: {query}")
                print(f"🎬 Title: {response.title or 'Unknown'}")
                print(f"🎭 Genres: {', '.join(response.inferred_genres)}")
                print(f"😊 Mood: {response.mood}")
                print(f"📊 Confidence: {response.confidence:.2f}")
                print("-" * 60)
                
                if logger:
                    logger.log_response(response, query, query_type="poster")
                
                return True
            except Exception as e:
                print(f"\n❌ Error analyzing poster: {e}")
                print("-" * 60)
                
                if logger:
                    logger.log_error(query, e, query_type="poster")
                
                return True
    
    return False


def main():
    """Main CLI loop."""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="Interactive CLI demo for Movie Agent Service",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use default log file (logs/cli_demo_TIMESTAMP.log)
  python demo/cli_demo.py

  # Specify custom log file
  python demo/cli_demo.py --log-file my_session.log

  # Disable logging
  python demo/cli_demo.py --no-log

Environment Variables:
  LOG_FILE: Path to log file (overridden by --log-file)
        """
    )
    parser.add_argument(
        "--log-file",
        type=str,
        help="Path to log file (default: logs/cli_demo_TIMESTAMP.log)"
    )
    parser.add_argument(
        "--no-log",
        action="store_true",
        help="Disable logging"
    )
    args = parser.parse_args()
    
    # Clean up old logs before starting
    cleanup_old_logs()
    
    # Setup logging
    logger = None
    log_file = None
    if not args.no_log:
        log_file = get_log_file_path(args.log_file)
        logger = InteractionLogger(log_file)
    
    # Create intent router (deterministic, no LLM)
    router = IntentRouter()
    
    print_banner(log_file)
    
    try:
        app = setup_app()
    except Exception as e:
        print(f"\n❌ Failed to initialize app: {e}")
        print("Please check your environment variables and configuration.")
        if logger:
            logger.log_error("initialization", e)
            logger.close()
        return 1
    
    # Generate a unique session ID for this CLI session (for memory isolation)
    import uuid
    session_id = str(uuid.uuid4())
    print(f"📝 Session ID: {session_id[:8]}... (for conversation memory)\n")
    
    # Interactive loop
    try:
        while True:
            try:
                query = input("You: ").strip()
                
                if not query:
                    continue
                
                # Check for exit commands
                if query.lower() in ['quit', 'exit', 'q']:
                    print("\n👋 Thanks for using Movie Agent Service! Goodbye!\n")
                    break
                
                # Route intent before agent call
                intent = router.route(query)
                
                # Handle greeting (no agent call needed)
                if intent == IntentType.GREETING:
                    print("\n👋 Hi! I can help you with:")
                    print("  • Movie recommendations and searches")
                    print("  • Movie quizzes and games")
                    print("  • Comparing movies")
                    print("  • Movie statistics")
                    print("  • Analyzing movie posters")
                    print("\nWhat would you like to do?\n")
                    print("-" * 60)
                    if logger:
                        logger.log_query(query, query_type="greeting")
                    continue
                
                # Handle unknown/misunderstood queries (no agent call)
                if intent == IntentType.UNKNOWN:
                    print("\n❓ I can help with:")
                    print("  • Movie searches (e.g., 'find sci-fi movies')")
                    print("  • Movie quizzes (e.g., 'play game' or 'quiz')")
                    print("  • Comparing movies (e.g., 'compare Inception vs Matrix')")
                    print("  • Statistics (e.g., 'stats movies by year')")
                    print("  • Poster analysis (e.g., 'analyze poster at path/to/image.png')")
                    print("\nPlease try a more specific query.\n")
                    print("-" * 60)
                    if logger:
                        logger.log_query(query, query_type="unknown")
                    continue
                
                # Handle poster analysis
                if intent == IntentType.POSTER_ANALYSIS:
                    if handle_poster_query(app, query, session_id, logger):
                        continue
                    # If poster extraction failed, fall through to agent
                
                # Handle game intent (route to quiz tools)
                if intent == IntentType.GAME:
                    # Let agent handle with quiz tools
                    if logger:
                        logger.log_query(query, query_type="game")
                    try:
                        # Pass session_id for memory continuity (same as Flask app)
                        response = app.chat(query, session_id=session_id)
                        print_response(response, query)
                        if logger:
                            logger.log_response(response, query, query_type="game")
                    except Exception as e:
                        print(f"\n❌ Error: {e}")
                        print("-" * 60)
                        if logger:
                            logger.log_error(query, e, query_type="game")
                    continue
                
                # Handle all other intents (movie search, compare, stats) via agent
                try:
                    if logger:
                        logger.log_query(query, query_type="chat")
                    
                    # Pass session_id for memory continuity (same as Flask app)
                    response = app.chat(query, session_id=session_id)
                    print_response(response, query)
                    
                    if logger:
                        logger.log_response(response, query, query_type="chat")
                except Exception as e:
                    print(f"\n❌ Error: {e}")
                    print("-" * 60)
                    
                    if logger:
                        logger.log_error(query, e, query_type="chat")
            
            except KeyboardInterrupt:
                print("\n\n👋 Interrupted. Goodbye!\n")
                break
            except EOFError:
                print("\n\n👋 Goodbye!\n")
                break
    finally:
        if logger:
            logger.close()
            print(f"\n📝 Session logged to: {log_file}\n")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

