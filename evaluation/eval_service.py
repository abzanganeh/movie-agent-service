from time import time
from src.movie_agent.service import MovieAgentService
from src.movie_agent.agent.prompts import MOVIE_REACT_PROMPT
from src.movie_agent.agent.output_parser import AgentOutputParser
from src.movie_agent.tools.impl import MovieSearchTool, PosterAnalysisTool
from src.movie_agent.schemas import ChatResponse

class EvalMovieAgentService(MovieAgentService):
    """Evaluation subclass for Step K, fully isolated."""

    def warmup(self):
        if self._agent:
            return

        # Use dummy tools for evaluation
        # Create tools from injected dummy retriever/vision_tool
        tools = []
        if self._vector_store:
            tools.append(MovieSearchTool(retriever=self._vector_store))
        if self._vision_analyst:
            tools.append(PosterAnalysisTool(vision_tool=self._vision_analyst))

        # Fill tool_names for the prompt
        prompt = MOVIE_REACT_PROMPT.partial(tool_names=[t.name for t in tools])

        # Use dummy LLM / prompt / memory for evaluation
        from langchain.memory import ConversationBufferMemory
        from langchain.agents import AgentExecutor, create_react_agent
        
        # Create the agent RunnableSequence
        agent_runnable = create_react_agent(
            llm=self.config.llm,
            tools=tools,
            prompt=prompt,
        )
        
        # Wrap in AgentExecutor to handle ReAct loop execution
        agent_executor = AgentExecutor(
            agent=agent_runnable,
            tools=tools,
            verbose=self.config.verbose,
            handle_parsing_errors=True
        )
        
        # Create a minimal wrapper to match MovieReactAgent interface
        class AgentWrapper:
            def __init__(self, executor):
                self.executor = executor
        
        self._agent = AgentWrapper(agent_executor)

    # Override chat to handle AgentExecutor
    def chat(self, user_message: str) -> ChatResponse:
        if not self._agent:
            raise RuntimeError("Agent not initialized")

        start_time = time()

        # AgentExecutor.invoke() expects dict with "input" key
        # Returns dict with "output" key
        result_dict = self._agent.executor.invoke({"input": user_message})
        
        # Extract the output string from the result
        raw_output = result_dict.get("output", str(result_dict))
        
        # Parse the output
        result = AgentOutputParser.parse(raw_output)
        latency_ms = int((time() - start_time) * 1000)

        return ChatResponse(
            answer=result["answer"],
            movies=result["movies"],
            latency_ms=latency_ms,
            reasoning_type="react",
        )
