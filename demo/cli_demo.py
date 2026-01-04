#!/usr/bin/env python3
"""
Interactive CLI demo for Movie Agent Service.

Provides a simple command-line interface to interact with the movie agent.
Demonstrates the agent's capabilities in a user-friendly way.
"""
import os
from dotenv import load_dotenv

# Imports assume PYTHONPATH=src is set (e.g., PYTHONPATH=src python demo/cli_demo.py)
from movie_agent.llm_factory import get_llm_instance
from movie_agent.vision_factory import create_vision_tool
from movie_agent.retriever_factory import create_retriever
from movie_agent.config import MovieAgentConfig
from movie_agent.vector_store import MovieVectorStore
from movie_agent.data_loader import MovieDataLoader
from movie_agent.canonicalizer import build_documents
from movie_agent.chunking import MovieChunker
from movie_agent.service import MovieAgentService

# Load environment variables
load_dotenv()


def print_banner():
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


def setup_service():
    """Set up and initialize the movie agent service."""
    print("🚀 Initializing Movie Agent Service...")
    
    # Load configuration
    config = MovieAgentConfig(
        movies_csv_path=os.getenv("MOVIE_DATA_CSV_PATH", "data/movies.csv"),
        warmup_on_start=False,
        enable_vision=True,
        vision_model_name=os.getenv("VISION_MODEL_NAME", "Salesforce/blip-image-captioning-base"),
        vision_model_path=os.getenv("VISION_MODEL_PATH", None),
        faiss_index_path=os.getenv("VECTOR_STORE_PATH", "movie_vectorstore"),
    )
    
    # Build vector store if it doesn't exist
    vector_store_path = config.faiss_index_path
    if not os.path.exists(vector_store_path):
        print(f"📦 Building FAISS index at {vector_store_path}...")
        
        embedding_provider = os.getenv("EMBEDDING_PROVIDER", "openai").lower()
        if embedding_provider == "openai":
            from langchain_openai import OpenAIEmbeddings
            embedding_model = OpenAIEmbeddings(openai_api_key=os.getenv("OPENAI_API_KEY"))
        else:
            raise ValueError(f"Unknown embedding provider: {embedding_provider}")
        
        loader = MovieDataLoader(config.movies_csv_path)
        movies = loader.load_movies()
        documents = build_documents(movies)
        
        chunker = MovieChunker()
        chunked_docs = chunker.chunk(documents)
        
        vector_store = MovieVectorStore(
            embedding_model=embedding_model,
            index_path=vector_store_path
        )
        vector_store.build_or_load(chunked_docs)
        print("✅ FAISS index built successfully!")
    
    # Create service
    service = MovieAgentService(config)
    
    # Inject production tools
    retriever = create_retriever(config=config)
    service.set_vector_store(retriever)
    
    vision_tool = create_vision_tool(config)
    service.set_vision_analyst(vision_tool)
    
    # Inject LLM
    config.llm = get_llm_instance(
        provider=config.llm_provider,
        model=config.llm_model
    )
    
    # Warmup
    print("🔥 Warming up agent...")
    service.warmup()
    print("✅ Ready!\n")
    
    return service


def handle_poster_query(service, query):
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
                response = service.analyze_poster(poster_path)
                print(f"\n📽️  Query: {query}")
                print(f"🎬 Title: {response.title or 'Unknown'}")
                print(f"🎭 Genres: {', '.join(response.inferred_genres)}")
                print(f"😊 Mood: {response.mood}")
                print(f"📊 Confidence: {response.confidence:.2f}")
                print("-" * 60)
                return True
            except Exception as e:
                print(f"\n❌ Error analyzing poster: {e}")
                print("-" * 60)
                return True
    
    return False


def main():
    """Main CLI loop."""
    print_banner()
    
    try:
        service = setup_service()
    except Exception as e:
        print(f"\n❌ Failed to initialize service: {e}")
        print("Please check your environment variables and configuration.")
        return 1
    
    # Interactive loop
    while True:
        try:
            query = input("You: ").strip()
            
            if not query:
                continue
            
            # Check for exit commands
            if query.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Thanks for using Movie Agent Service! Goodbye!\n")
                break
            
            # Handle poster queries
            if handle_poster_query(service, query):
                continue
            
            # Handle regular chat queries
            try:
                response = service.chat(query)
                print_response(response, query)
            except Exception as e:
                print(f"\n❌ Error: {e}")
                print("-" * 60)
        
        except KeyboardInterrupt:
            print("\n\n👋 Interrupted. Goodbye!\n")
            break
        except EOFError:
            print("\n\n👋 Goodbye!\n")
            break
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

