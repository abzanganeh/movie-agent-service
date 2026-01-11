"""
Hugging Face Spaces deployment for Movie Agent Service.

This Gradio app provides a web interface for the Movie Agent Service.
It supports both chat queries and poster image analysis.
"""
import os
import sys
import logging
from pathlib import Path
import gradio as gr

# Add the service to Python path
# In Spaces, the structure is: spaces/app.py, but src/ is at the repo root
current_dir = Path(__file__).parent
if (current_dir / "src").exists():
    # Running in Spaces deployment (src/ in same directory)
    service_path = current_dir / "src"
else:
    # Running locally (src/ is parent of spaces/)
    service_path = current_dir.parent / "src"
sys.path.insert(0, str(service_path))

from movie_agent.app import MovieAgentApp
from movie_agent.config import MovieAgentConfig

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global agent instance
agent_app: MovieAgentApp = None


def initialize_agent():
    """Initialize the movie agent service."""
    global agent_app
    
    if agent_app is not None:
        return agent_app
    
    try:
        # Configuration for Hugging Face Spaces
        # Environment variables should be set in Spaces secrets
        current_dir = Path(__file__).parent
        data_path = current_dir / "data" / "movies.csv"
        if not data_path.exists():
            # Try parent directory
            data_path = current_dir.parent / "data" / "movies.csv"
        
        vector_store_path = current_dir / "movie_vectorstore"
        if not vector_store_path.exists():
            vector_store_path = current_dir.parent / "movie_vectorstore"
        
        config = MovieAgentConfig(
            # Paths - use absolute paths for Spaces
            movies_csv_path=str(data_path),
            faiss_index_path=str(vector_store_path),
            
            # LLM Configuration
            llm_provider=os.getenv("LLM_PROVIDER", "groq"),
            llm_model=os.getenv("LLM_MODEL", "llama-3.1-8b-instant"),
            
            # Hardware
            device=os.getenv("DEVICE", "auto"),
            force_cpu=os.getenv("FORCE_CPU", "false").lower() == "true",
            log_hardware_info=True,
            
            # Features
            enable_vision=os.getenv("ENABLE_VISION", "true").lower() == "true",
            enable_memory=os.getenv("ENABLE_MEMORY", "true").lower() == "true",
            memory_max_turns=int(os.getenv("MEMORY_MAX_TURNS", "10")),
            
            # Performance
            warmup_on_start=True,
            verbose=False,
        )
        
        agent_app = MovieAgentApp(config)
        agent_app.initialize()
        logger.info("Movie Agent Service initialized successfully")
        return agent_app
        
    except Exception as e:
        logger.error(f"Failed to initialize agent: {e}", exc_info=True)
        raise


def chat_interface(query: str, history: list) -> tuple[str, list]:
    """
    Handle chat queries.
    
    :param query: User query
    :param history: Conversation history
    :return: Response and updated history
    """
    global agent_app
    
    if agent_app is None:
        try:
            initialize_agent()
        except Exception as e:
            return f"Error: Failed to initialize agent. {str(e)}", history
    
    if not query or not query.strip():
        return "", history
    
    try:
        # Generate session ID from history length (simple approach)
        session_id = f"hf_space_{len(history)}"
        
        # Get response from agent
        response = agent_app.chat(query, session_id=session_id)
        
        # Format response
        answer = response.answer
        if response.movies:
            movie_list = "\n".join([
                f"- {m.title} ({m.year})" for m in response.movies[:5]
            ])
            answer = f"{answer}\n\n**Movies Found:**\n{movie_list}"
        
        # Update history
        history.append((query, answer))
        return "", history
        
    except Exception as e:
        error_msg = f"Error: {str(e)}"
        logger.error(error_msg, exc_info=True)
        history.append((query, error_msg))
        return "", history


def analyze_poster(image) -> str:
    """
    Analyze a movie poster image.
    
    :param image: PIL Image or file path
    :return: Analysis results
    """
    global agent_app
    
    if agent_app is None:
        try:
            initialize_agent()
        except Exception as e:
            return f"Error: Failed to initialize agent. {str(e)}"
    
    if image is None:
        return "Please upload a movie poster image."
    
    try:
        # Save image temporarily
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_file:
            if hasattr(image, "save"):
                # PIL Image
                image.save(tmp_file.name)
            else:
                # File path
                import shutil
                shutil.copy(image, tmp_file.name)
            
            image_path = tmp_file.name
        
        # Analyze poster
        session_id = "hf_space_poster"
        response = agent_app.analyze_poster(image_path, session_id=session_id)
        
        # Format response
        result = f"**Analysis Results:**\n\n"
        result += f"**Caption:** {response.caption}\n\n"
        
        if response.inferred_genres:
            result += f"**Genres:** {', '.join(response.inferred_genres)}\n\n"
        
        result += f"**Mood:** {response.mood}\n\n"
        result += f"**Confidence:** {response.confidence:.2%}\n\n"
        
        if response.title:
            result += f"**Identified Movie:** {response.title}\n"
        
        # Cleanup
        os.unlink(image_path)
        
        return result
        
    except Exception as e:
        error_msg = f"Error analyzing poster: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return error_msg


# Initialize agent on startup
try:
    initialize_agent()
except Exception as e:
    logger.warning(f"Agent initialization deferred: {e}")


# Create Gradio interface
with gr.Blocks(title="Movie Agent Service", theme=gr.themes.Soft()) as demo:
    gr.Markdown("""
    # 🎬 Movie Agent Service
    
    An AI-powered movie discovery and analysis service using RAG and tool-calling agents.
    
    **Features:**
    - 🔍 Semantic movie search
    - 📊 Movie statistics and comparisons
    - 🎨 Poster image analysis
    - 💬 Conversational interface
    """)
    
    with gr.Tabs():
        with gr.TabItem("💬 Chat"):
            chatbot = gr.Chatbot(
                label="Conversation",
                height=500,
                show_copy_button=True
            )
            msg = gr.Textbox(
                label="Ask about movies",
                placeholder="e.g., 'Find sci-fi movies from the 2000s' or 'What are the top rated action movies?'",
                lines=2
            )
            with gr.Row():
                submit_btn = gr.Button("Send", variant="primary")
                clear_btn = gr.Button("Clear")
            
            msg.submit(chat_interface, [msg, chatbot], [msg, chatbot])
            submit_btn.click(chat_interface, [msg, chatbot], [msg, chatbot])
            clear_btn.click(lambda: ([], ""), None, [chatbot, msg])
        
        with gr.TabItem("🎨 Poster Analysis"):
            gr.Markdown("Upload a movie poster image to analyze its visual elements and identify the movie.")
            poster_image = gr.Image(
                label="Movie Poster",
                type="pil",
                height=400
            )
            analyze_btn = gr.Button("Analyze Poster", variant="primary")
            poster_result = gr.Textbox(
                label="Analysis Results",
                lines=10,
                interactive=False
            )
            analyze_btn.click(analyze_poster, poster_image, poster_result)
    
    gr.Markdown("""
    ### Configuration
    
    Make sure to set the following environment variables in your Space settings:
    - `GROQ_API_KEY` or `OPENAI_API_KEY` (for LLM)
    - `OPENAI_API_KEY` (for embeddings, if using OpenAI embeddings)
    
    See the README for more details.
    """)


if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False
    )
