from typing import List, Optional
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory
from langchain.tools import BaseTool
from .output_parser import AgentOutputParser
from .prompts import MOVIE_REACT_PROMPT


class MovieReactAgent:
    """
    Encapsulates ReAct-based reasoning for the Movie AI Agent.
    """
    
    def __init__(self,
                 llm,
                 tools: List[BaseTool],
                 prompt: Optional[PromptTemplate] = None,
                 memory=None,
                 verbose: bool = False):
        self._llm = llm
        self._tools = tools
        self._prompt = prompt or MOVIE_REACT_PROMPT.partial(tool_names=[t.name for t in tools])
        self._memory = memory or ConversationBufferMemory(memory_key="chat_history", return_messages=True)
        self._verbose = verbose
        self.executor: Optional[AgentExecutor] = None

        # Build the agent immediately
        self._build_executor()
        
    def _build_executor(self):
        """
        Constructs a LangChain ReAct agent with provided tools, prompt, and memory.
        """
        agent_runnable = create_react_agent(
            llm=self._llm,
            tools=self._tools,
            prompt=self._prompt,
        )
        
        # Wrap in AgentExecutor for v0.3+ compatibility
        self.executor = AgentExecutor(
            agent=agent_runnable,
            tools=self._tools,
            verbose=self._verbose,
            handle_parsing_errors=True
        )
        
    def run(self, user_query: str) -> dict:
        """
        Executes the ReAct reasoning loop and returns structured output.
        Uses invoke() for LangChain v0.3+ compatibility.
        """
        if not self.executor:
            raise RuntimeError("Agent executor not initialized.")

        # Use invoke() for v0.3+ compatibility
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