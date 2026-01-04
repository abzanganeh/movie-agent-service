from src.movie_agent.config import MovieAgentConfig
from evaluation.eval_service import EvalMovieAgentService
from evaluation.dummy_tools import DummyRetriever, DummyVisionTool
from evaluation.dummy_llm import DummyChatModel

# Step 1 — Evaluation config
config = MovieAgentConfig(
    movies_csv_path="data/movies.csv",
    warmup_on_start=False,
    enable_vision=True
)
config.llm = DummyChatModel()  # LangChain-compatible dummy chat model
config.verbose = False  # Disable verbose output for cleaner evaluation

# Step 2 — Create evaluation service
service = EvalMovieAgentService(config)

# Step 3 — Inject dummy tools
service.set_vector_store(DummyRetriever())
service.set_vision_analyst(DummyVisionTool())

# Step 4 — Warmup safely
service.warmup()

# Step 5 — Run sample queries
queries = [
    "Recommend sci-fi movies like Inception",
    "Find action movies from 2020 onwards",
    "Analyze poster at path /tmp/dummy_poster.jpg"
]

for q in queries:
    if q.startswith("Analyze poster"):
        poster_path = q.split()[-1]
        res = service.analyze_poster(poster_path)
    else:
        res = service.chat(q)
    print(f"Query: {q}")
    print("Result:", res)
    print("-" * 50)
