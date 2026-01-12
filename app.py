#!/usr/bin/env python3
"""
Flask REST API for Movie Agent Service - Hugging Face Spaces Deployment.

Adapted for Docker deployment on Hugging Face Spaces.
Uses environment variables for configuration (no encrypted config file needed).
"""
import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional
from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from dotenv import load_dotenv

# Rate limiting (optional - gracefully handles if not installed)
try:
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address
    RATE_LIMITING_AVAILABLE = True
except ImportError:
    RATE_LIMITING_AVAILABLE = False
    class Limiter:
        def __init__(self, *args, **kwargs):
            pass
        def limit(self, *args, **kwargs):
            def decorator(f):
                return f
            return decorator
    def get_remote_address():
        return "unknown"

# Add service to path (for Spaces, src/ is in the same directory)
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Public API imports
from movie_agent.app import MovieAgentApp
from movie_agent.config import MovieAgentConfig
from movie_agent.interaction import IntentRouter, IntentType
from movie_agent.security import InputValidator, FileValidator, ValidationError

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", os.urandom(32).hex())

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Security: Rate limiting
if RATE_LIMITING_AVAILABLE:
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=["100 per hour", "10 per minute"],
        storage_uri="memory://",
    )
    logger.info("Rate limiting enabled")
else:
    limiter = Limiter()
    logger.warning("Rate limiting not available")

# Global instances
intent_router = IntentRouter()
agent_app: Optional[MovieAgentApp] = None


def _initialize_agent_from_env():
    """Initialize agent from environment variables (for Spaces deployment)."""
    global agent_app
    
    if agent_app is not None:
        return
    
    try:
        # Get configuration from environment variables
        llm_provider = os.getenv("LLM_PROVIDER", "groq")
        llm_model = os.getenv("LLM_MODEL", "llama-3.1-8b-instant" if llm_provider == "groq" else "gpt-4o-mini")
        
        # API keys should be set as environment variables (Spaces secrets)
        if llm_provider == "groq" and not os.getenv("GROQ_API_KEY"):
            logger.warning("GROQ_API_KEY not found in environment")
        if not os.getenv("OPENAI_API_KEY"):
            logger.warning("OPENAI_API_KEY not found (needed for embeddings)")
        
        # Create config object
        config = MovieAgentConfig(
            llm_provider=llm_provider,
            llm_model=llm_model,
            enable_vision=os.getenv("ENABLE_VISION", "true").lower() == "true",
            enable_memory=os.getenv("ENABLE_MEMORY", "true").lower() == "true",
            memory_max_turns=int(os.getenv("MEMORY_MAX_TURNS", "10")),
            faiss_index_path="movie_vectorstore",
            movies_csv_path="data/movies.csv",
            warmup_on_start=True,
            verbose=False,
            device=os.getenv("DEVICE", "auto"),
            force_cpu=os.getenv("FORCE_CPU", "false").lower() == "true",
        )
        
        # Initialize agent app
        agent_app = MovieAgentApp(config)
        agent_app.initialize()
        logger.info("Agent initialized successfully from environment variables")
        
    except Exception as e:
        logger.error(f"Failed to initialize agent: {str(e)}", exc_info=True)
        agent_app = None


# Initialize on startup (for Spaces)
_initialize_agent_from_env()


@app.route("/")
def index():
    """Serve main UI."""
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
@limiter.limit("20 per minute")
def chat():
    """Chat endpoint."""
    try:
        if agent_app is None:
            return jsonify({"error": "Agent not initialized. Please check configuration."}), 500
        
        data = request.get_json()
        if not data or "query" not in data:
            return jsonify({"error": "Missing 'query' in request body"}), 400
        
        query = data["query"].strip()
        if not query:
            return jsonify({"error": "Empty query"}), 400
        
        # Security: Validate input
        try:
            query = InputValidator.sanitize_query(query)
        except ValidationError as e:
            logger.warning(f"Input validation failed: {str(e)}")
            return jsonify({"error": str(e)}), 400
        
        # Route intent
        intent = intent_router.route(query)
        
        # Get or create session ID
        import uuid
        if 'session_id' not in session:
            session['session_id'] = str(uuid.uuid4())
        session_id = session['session_id']
        
        logger.info(f"Chat query - Session: {session_id}, Intent: {intent.name}")
        
        response = agent_app.chat(query, session_id=session_id)
        logger.info(f"Chat response - Session: {session_id}, Tools: {response.tools_used}, Latency: {response.latency_ms}ms")
        
        result = {
            "answer": response.answer,
            "movies": response.movies,
            "tools_used": response.tools_used,
            "llm_latency_ms": response.llm_latency_ms,
            "tool_latency_ms": response.tool_latency_ms,
            "latency_ms": response.latency_ms,
            "reasoning_type": response.reasoning_type,
        }
        
        if response.resolution_metadata:
            result["resolution_metadata"] = response.resolution_metadata
        
        if response.quiz_data:
            result["quiz_data"] = response.quiz_data
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Chat endpoint error: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/poster", methods=["POST"])
@limiter.limit("10 per minute")
def poster():
    """Poster analysis endpoint."""
    if agent_app is None:
        return jsonify({"error": "Agent not initialized. Please check configuration."}), 500
    
    try:
        if "image" not in request.files:
            return jsonify({"error": "Missing 'image' file in form data"}), 400
        
        file = request.files["image"]
        if not file.filename:
            return jsonify({"error": "Empty file"}), 400
        
        # Save to temp file
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp:
            file.save(tmp.name)
            tmp_path = tmp.name
        
        # Validate file
        is_valid, error_msg = FileValidator.validate_image_file(tmp_path)
        if not is_valid:
            os.unlink(tmp_path)
            logger.warning(f"File validation failed: {error_msg}")
            return jsonify({"error": f"File validation failed: {error_msg}"}), 400
        
        try:
            # Get or create session ID
            import uuid
            if 'session_id' not in session:
                session['session_id'] = str(uuid.uuid4())
            session_id = session['session_id']
            
            logger.info(f"Analyzing poster - Session: {session_id}, File: {file.filename}")
            
            poster_response = agent_app.analyze_poster(tmp_path, session_id=session_id)
            
            logger.info(f"Poster analysis result - Session: {session_id}, Title: {poster_response.title}, Confidence: {poster_response.confidence}")
            
            # Store in session for UI
            session['poster_state'] = {
                "title": poster_response.title,
                "mood": poster_response.mood,
                "confidence": poster_response.confidence,
                "caption": poster_response.caption,
                "timestamp": datetime.now().isoformat(),
            }
            
            return jsonify({
                "title": poster_response.title,
                "caption": poster_response.caption,
                "mood": poster_response.mood,
                "confidence": poster_response.confidence,
                "inferred_genres": poster_response.inferred_genres,
            })
        finally:
            os.unlink(tmp_path)
    
    except Exception as e:
        logger.error(f"Poster analysis error: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/about")
def about():
    """Serve About page."""
    return render_template("about.html")


@app.route("/clear-poster", methods=["POST"])
def clear_poster():
    """Clear poster state from session."""
    try:
        import uuid
        if 'session_id' not in session:
            session['session_id'] = str(uuid.uuid4())
        session_id = session['session_id']
        
        if agent_app and hasattr(agent_app, '_service'):
            agent_app._service.clear_memory(session_id)
        
        session.pop('poster_state', None)
        session.pop('poster_history', None)
        logger.info(f"Cleared poster_state - Session: {session_id}")
        
        return jsonify({"status": "success", "message": "Poster state cleared"})
    except Exception as e:
        logger.error(f"Error clearing poster state: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    # Hugging Face Spaces provides PORT environment variable
    port = int(os.getenv("PORT", 7860))
    # Disable debug mode for production
    app.run(host="0.0.0.0", port=port, debug=False)
