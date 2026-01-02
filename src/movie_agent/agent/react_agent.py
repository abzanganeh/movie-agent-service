from typing import List, Optional
from langchain_core.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate
from langchain_core.memory import ConversationBufferMemory
from langchain_core.schema import BaseOutputParser
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
                 prompt: str, 
                 memory: Optional[ConversationBufferMemory] = None,
                 verbose: bool = False,
                 ):
        self._llm = llm
        self._tools = tools
        self._prompt = prompt
        self._memory = memory or ConversationBufferMemory(memory_key="chat_history", return_messages=True)
        self._verbose = verbose     
        self.executor = Optional[AgentExecutor] = None

                # Build the agent immediately
        self._build_executor()
        
    def _build_executor(self):
        """
        Constructs a LangChain ReAct agent with provided tools, prompt, and memory.
        """
        self.executor = create_react_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=MOVIE_REACT_PROMPT,
            verbose=self.verbose,
            memory=self.memory,
        )
    
    def run(self, user_query: str) -> dict:
        """
        Executes the ReAct reasoning loop and returns structured output.
        """
        if not self.executor:
            raise RuntimeError("Agent executor not initialized.")

        raw_output = self.executor.run(user_query)
        return AgentOutputParser.parse(raw_output)


    async def arun(self, user_query: str) -> dict:
        """
        Async interface for LangChain compatibility.
        """
        if not self.executor:
            raise RuntimeError("Agent executor not initialized.")

        raw_output = await self.executor.arun(user_query)
        return AgentOutputParser.parse(raw_output)