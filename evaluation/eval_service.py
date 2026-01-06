from time import time
from src.movie_agent.service import MovieAgentService
from src.movie_agent.agent.prompts import MOVIE_PROMPT
from src.movie_agent.agent.output_parser import AgentOutputParser
from src.movie_agent.agent.callbacks import ToolLatencyCallback
from src.movie_agent.tools.impl import MovieSearchTool, PosterAnalysisTool
from src.movie_agent.schemas import ChatResponse

class EvalMovieAgentService(MovieAgentService):
    """Evaluation subclass for Step K, fully isolated."""

    def warmup(self):
        if self._agent:
            return

        # Create tools from injected retriever/vision_tool
        tools = []
        if self._vector_store:
            tools.append(MovieSearchTool(retriever=self._vector_store))
        if self._vision_analyst:
            tools.append(PosterAnalysisTool(vision_tool=self._vision_analyst))

        prompt = MOVIE_PROMPT.partial(tool_names=[t.name for t in tools])

        from langchain.agents import AgentExecutor, create_openai_tools_agent

        agent_runnable = create_openai_tools_agent(
            llm=self.config.llm,
            tools=tools,
            prompt=prompt,
        )

        agent_executor = AgentExecutor(
            agent=agent_runnable,
            tools=tools,
            verbose=self.config.verbose,
            handle_parsing_errors=True,
            max_iterations=2,  # Allow tool call + final answer, prevent further loops
        )

        self._agent = agent_executor

    # Override chat to handle AgentExecutor
    def chat(self, user_message: str) -> ChatResponse:
        if not self._agent:
            raise RuntimeError("Agent not initialized")

        # Create callback handler for tool latency tracking
        tool_callback = ToolLatencyCallback()
        
        start_time = time()

        # AgentExecutor.invoke() expects dict with "input" key
        # Returns dict with "output" key
        result_dict = self._agent.invoke(
            {"input": user_message},
            config={"callbacks": [tool_callback]}
        )
        
        # Extract the output string from the result
        raw_output = result_dict.get("output", str(result_dict))
        
        # Parse the output
        result = AgentOutputParser.parse(raw_output)
        total_latency_ms = int((time() - start_time) * 1000)
        
        # Get precise tool execution time from callback
        tool_latency_ms = tool_callback.get_total_tool_latency_ms()
        
        # Calculate pure LLM time (total - tool time)
        pure_llm_latency_ms = max(0, total_latency_ms - tool_latency_ms)

        return ChatResponse(
            answer=result["answer"],
            movies=result["movies"],
            tools_used=result.get("tools_used", []),
            llm_latency_ms=pure_llm_latency_ms,
            tool_latency_ms=tool_latency_ms,
            latency_ms=total_latency_ms,
            reasoning_type="tool_calling",
        )
