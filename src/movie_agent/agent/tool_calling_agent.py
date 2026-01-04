from typing import List, Optional
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.prompts import PromptTemplate
from langchain.tools import BaseTool
from .output_parser import AgentOutputParser
from .prompts import MOVIE_REACT_PROMPT


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
        
        self.executor = AgentExecutor(
            agent=agent_runnable,
            tools=self._tools,
            verbose=self._verbose,
            handle_parsing_errors=True,
        )
        
    def run(self, user_query: str) -> dict:
        """
        Executes a single tool call and returns structured output.
        """
        if not self.executor:
            raise RuntimeError("Agent executor not initialized.")

        result_dict = self.executor.invoke({"input": user_query})
        raw_output = result_dict.get("output", str(result_dict))
        return AgentOutputParser.parse(raw_output)


    async def arun(self, user_query: str) -> dict:
        """
        Async interface for LangChain compatibility.
        """
        if not self.executor:
            raise RuntimeError("Agent executor not initialized.")

        result_dict = await self.executor.ainvoke({"input": user_query})
        raw_output = result_dict.get("output", str(result_dict))
        return AgentOutputParser.parse(raw_output)