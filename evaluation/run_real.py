# evaluation/run_real.py
import os
from time import time
from dotenv import load_dotenv
from src.movie_agent.llm_factory import get_llm_instance
from src.movie_agent.vision_factory import create_vision_tool
from src.movie_agent.retriever_factory import create_retriever
from src.movie_agent.resolution import create_title_resolver
from src.movie_agent.config import MovieAgentConfig
from src.movie_agent.vector_store import MovieVectorStore
from src.movie_agent.data_loader import MovieDataLoader
from src.movie_agent.canonicalizer import build_documents
from src.movie_agent.chunking import MovieChunker
from evaluation.eval_service import EvalMovieAgentService

# Load .env
load_dotenv()

# Step 1 — Config
config = MovieAgentConfig(
    movies_csv_path=os.getenv("MOVIE_DATA_CSV_PATH", "data/movies.csv"),
    warmup_on_start=False,
    enable_vision=True,
    vision_model_name=os.getenv("VISION_MODEL_NAME", "Salesforce/blip-image-captioning-base"),
    vision_model_path=os.getenv("VISION_MODEL_PATH", None),
    faiss_index_path=os.getenv("VECTOR_STORE_PATH", "movie_vectorstore"),
)

# Step 1.5 — Build vector store if it doesn't exist
vector_store_path = config.faiss_index_path
if not os.path.exists(vector_store_path):
    print(f"Building FAISS index at {vector_store_path}...")
    
    # Create embedding model
    embedding_provider = os.getenv("EMBEDDING_PROVIDER", "openai").lower()
    if embedding_provider == "openai":
        from langchain_openai import OpenAIEmbeddings
        embedding_model = OpenAIEmbeddings(openai_api_key=os.getenv("OPENAI_API_KEY"))
    else:
        raise ValueError(f"Unknown embedding provider: {embedding_provider}")
    
    # Load movies and build index
    loader = MovieDataLoader(config.movies_csv_path)
    movies = loader.load_movies()
    documents = build_documents(movies)
    
    # Chunk documents
    chunker = MovieChunker()
    chunked_docs = chunker.chunk(documents)
    
    # Build vector store
    vector_store = MovieVectorStore(
        embedding_model=embedding_model,
        index_path=vector_store_path
    )
    vector_store.build_or_load(chunked_docs)
    print("FAISS index built successfully!")

# Step 2 — Service instance
service = EvalMovieAgentService(config)

# Step 3 — Build semantic resolver (for query correction and title inference)
title_resolver = create_title_resolver(config=config)

# Step 4 — Inject production tools using factories

# FAISS-backed Retriever - factory handles embedding model creation
# Inject title_resolver for query correction and entity normalization
retriever = create_retriever(config=config, title_resolver=title_resolver)
service.set_vector_store(retriever)

# Vision tool - using factory function (pure vision - no title inference)
# Movie identification is agent's responsibility via movie_search
vision_tool = create_vision_tool(config=config)
service.set_vision_analyst(vision_tool)

# Step 5 — Inject LLM using factory
config.llm = get_llm_instance(
    provider=config.llm_provider,
    model=config.llm_model
)

# Step 6 — Warmup
service.warmup()

# Step 7 — Evaluation queries
queries = [
    "Recommend sci-fi movies like Inception",
    "Find action movies from 2020 onwards",
    "Analyze poster at path data/posters/test_poster01.png"
]

for q in queries:
    start = time()
    if "poster" in q.lower():
        res = service.analyze_poster("data/posters/test_poster01.png")
    else:
        res = service.chat(q)
    latency = int((time() - start) * 1000)
    print(f"Query: {q}\nResult: {res}\nLatency(ms): {latency}\n{'-'*50}")