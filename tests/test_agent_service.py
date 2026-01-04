from src.movie_agent.service import MovieAgentService
from src.movie_agent.config import MovieAgentConfig


class FakeAgent:
    def run(self, input: str) -> dict:
        return {
            "answer": "Agent response",
            "movies": [],
            "tools_used": [],
            "llm_latency_ms": None,
            "tool_latency_ms": None,
        }


def test_agent_service_chat_executes_agent():
    config = MovieAgentConfig(
        movies_csv_path="dummy.csv",
        warmup_on_start=False
    )

    service = MovieAgentService(config)

    # Inject fake agent directly
    service._agent = FakeAgent()

    response = service.chat("recommend a movie")

    assert response.answer == "Agent response"
    assert response.reasoning_type == "tool_calling"
    assert response.tools_used == []
    assert response.llm_latency_ms is None
    assert response.tool_latency_ms is None
    assert response.latency_ms >= 0
