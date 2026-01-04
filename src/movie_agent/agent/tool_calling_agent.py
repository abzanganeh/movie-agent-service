from typing import List, Optional, Dict, Any
from time import time
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.prompts import PromptTemplate
from langchain.tools import BaseTool
from .output_parser import AgentOutputParser
from .prompts import MOVIE_REACT_PROMPT
from .callbacks import ToolLatencyCallback


class ToolCallingAgent:
    """
    Single-tool calling agent (no ReAct loop).
    Chooses exactly one tool based on the prompt and returns a parsed result.
    """
    
    def __init__(self,
                 llm,
                 tools: List[BaseTool],
                 prompt: Optional[PromptTemplate] = None,
                 verbose: bool = False):
        self._llm = llm
        self._tools = tools
        self._prompt = prompt or MOVIE_REACT_PROMPT.partial(tool_names=[t.name for t in tools])
        self._verbose = verbose
        self.executor: Optional[AgentExecutor] = None

        # Build the agent immediately
        self._build_executor()
        
    def _build_executor(self):
        """
        Constructs a LangChain tool-calling agent with provided tools and prompt.
        """
        # Bind tools with auto tool choice to reduce function-call errors
        llm_with_tools = self._llm.bind_tools(self._tools, tool_choice="auto")

        agent_runnable = create_openai_tools_agent(
            llm=llm_with_tools,
            tools=self._tools,
            prompt=self._prompt,
        )
        
        # Enforce single-tool call: max_iterations prevents infinite loops
        # Tool-calling agents typically need 2 steps: tool call + final answer generation
        # Setting to 5 allows some flexibility while preventing infinite loops
        self.executor = AgentExecutor(
            agent=agent_runnable,
            tools=self._tools,
            verbose=self._verbose,
            handle_parsing_errors=True,
            max_iterations=5,  # Allow tool call + final answer, prevent infinite loops
        )
        
    def run(self, user_query: str) -> Dict[str, Any]:
        """
        Executes a single tool call and returns structured output with latency tracking.
        
        Uses LangChain callbacks to capture precise tool execution time.
        """
        if not self.executor:
            raise RuntimeError("Agent executor not initialized.")

        # Create callback handler for tool latency tracking
        tool_callback = ToolLatencyCallback()
        
        # Track total execution time (LLM + tools)
        total_start = time()
        
        # Track LLM latency (agent planning + generation)
        # Note: This includes LLM time, but tool time is tracked separately via callbacks
        llm_start = time()
        result_dict = self.executor.invoke(
            {"input": user_query},
            config={"callbacks": [tool_callback]}
        )
        llm_latency_ms = int((time() - llm_start) * 1000)
        
        # Get precise tool execution time from callback
        tool_latency_ms = tool_callback.get_total_tool_latency_ms()
        
        # Calculate pure LLM time (total - tool time)
        # This gives us LLM planning/generation time excluding tool execution
        pure_llm_latency_ms = max(0, llm_latency_ms - tool_latency_ms)

        raw_output = result_dict.get("output", str(result_dict))
        parsed = AgentOutputParser.parse(raw_output)
        
        # Store latency breakdown
        parsed["llm_latency_ms"] = pure_llm_latency_ms
        parsed["tool_latency_ms"] = tool_latency_ms
        
        return parsed


    async def arun(self, user_query: str) -> Dict[str, Any]:
        """
        Async interface for LangChain compatibility with latency tracking.
        """
        if not self.executor:
            raise RuntimeError("Agent executor not initialized.")

        # Create callback handler for tool latency tracking
        tool_callback = ToolLatencyCallback()
        
        llm_start = time()
        result_dict = await self.executor.ainvoke(
            {"input": user_query},
            config={"callbacks": [tool_callback]}
        )
        llm_latency_ms = int((time() - llm_start) * 1000)
        
        # Get precise tool execution time from callback
        tool_latency_ms = tool_callback.get_total_tool_latency_ms()
        pure_llm_latency_ms = max(0, llm_latency_ms - tool_latency_ms)

        raw_output = result_dict.get("output", str(result_dict))
        parsed = AgentOutputParser.parse(raw_output)
        
        # Store latency breakdown
        parsed["llm_latency_ms"] = pure_llm_latency_ms
        parsed["tool_latency_ms"] = tool_latency_ms
        
        return parsed