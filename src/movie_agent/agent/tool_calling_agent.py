from typing import List, Optional, Dict, Any
from time import time
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.prompts import PromptTemplate
from langchain.tools import BaseTool
from .output_parser import AgentOutputParser
from .prompts import MOVIE_PROMPT
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
        self._prompt = prompt or MOVIE_PROMPT.partial(
            tool_names=[t.name for t in tools],
            chat_history=""
        )
        self._verbose = verbose
        self.executor: Optional[AgentExecutor] = None

        self._build_executor()
        
    def _build_executor(self):
        """Constructs a LangChain tool-calling agent with provided tools and prompt."""
        # For function-calling, tools must be bound to LLM
        # tool_choice="auto" allows LLM to decide when to call tools
        # Note: Groq may have compatibility issues with function-calling
        # We bind tools to enable structured function calls (not text generation)
        try:
            llm_with_tools = self._llm.bind_tools(self._tools, tool_choice="auto")
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to bind tools to LLM: {e}. Falling back to direct LLM.")
            llm_with_tools = self._llm

        # create_openai_tools_agent uses function-calling API automatically
        # This should work with OpenAI-compatible LLMs
        # If Groq doesn't support function-calling properly, this may fail
        agent_runnable = create_openai_tools_agent(
            llm=llm_with_tools,
            tools=self._tools,
            prompt=self._prompt,
        )
        
        executor_kwargs = {
            "agent": agent_runnable,
            "tools": self._tools,
            "verbose": self._verbose,
            "handle_parsing_errors": True,
            "max_iterations": 1,  # Single tool call only - tool output is final answer
            "max_execution_time": 30,
            "return_intermediate_steps": True,
        }
        
        # Try to add early_stopping_method if supported (LangChain 0.1+)
        try:
            import inspect
            sig = inspect.signature(AgentExecutor.__init__)
            if "early_stopping_method" in sig.parameters:
                executor_kwargs["early_stopping_method"] = "force"
        except Exception:
            # Fallback: max_iterations=2 is sufficient for single-tool agents
            pass
        
        self.executor = AgentExecutor(**executor_kwargs)
    
    def _extract_tool_output(self, intermediate_steps: list, raw_output: str) -> Dict[str, Any]:
        """
        Extract and format tool output when agent stops at max_iterations.
        
        This handles the case where the agent calls a tool but doesn't format
        a final answer because max_iterations=1 prevents a second step.
        """
        import re
        import json
        
        tools_used = []
        tool_outputs = []
        movies = []
        quiz_data = None
        
        for step in intermediate_steps:
            if len(step) >= 2:
                tool_action = step[0]
                tool_output = step[1]
                
                # Extract tool name
                tool_name = getattr(tool_action, 'tool', None) or str(tool_action).split('(')[0]
                if tool_name:
                    tools_used.append(tool_name)
                
                # Extract tool output
                if isinstance(tool_output, str):
                    tool_outputs.append(tool_output)
                    
                    # Parse movie_search output: "Title (Year); Title (Year); ..."
                    if tool_name == 'movie_search':
                        # Extract movie titles and years
                        pattern = r'([^(]+)\s*\((\d{4})\)'
                        matches = re.findall(pattern, tool_output)
                        for title, year in matches:
                            # Store as string (title only) to match expected format
                            movies.append(title.strip())
                    
                    # Parse generate_movie_quiz output: JSON with questions
                    elif tool_name == 'generate_movie_quiz':
                        try:
                            quiz_data = json.loads(tool_output)
                        except (json.JSONDecodeError, Exception):
                            # If JSON parsing fails, try to extract from text
                            json_match = re.search(r'\{.*\}', tool_output, re.DOTALL)
                            if json_match:
                                try:
                                    quiz_data = json.loads(json_match.group())
                                except Exception:
                                    pass
                    
                    # Parse check_quiz_answer output: JSON with feedback
                    elif tool_name == 'check_quiz_answer':
                        try:
                            check_result = json.loads(tool_output)
                            # Format the feedback nicely
                            is_correct = check_result.get("is_correct", False)
                            correct_answer = check_result.get("correct_answer", "")
                            if is_correct:
                                formatted_feedback = f"Correct! Great job! The answer was {correct_answer}."
                            else:
                                formatted_feedback = f"Incorrect. The correct answer was {correct_answer}. Let's try the next one!"
                            # Replace JSON with formatted message
                            tool_outputs[-1] = formatted_feedback
                        except (json.JSONDecodeError, Exception):
                            # If parsing fails, keep original output
                            pass
        
        # Format answer from tool output
        if tool_outputs:
            answer = tool_outputs[-1]  # Use last tool output
            
            # Quiz data is handled by service layer - just pass through
            # Service will serve one question at a time
            if quiz_data and 'questions' in quiz_data:
                topic = quiz_data.get('topic', 'movies')
                questions = quiz_data.get('questions', [])
                if questions:
                    # Simple message - service will handle structured response
                    answer = f"Quiz generated: {topic} ({len(questions)} questions)"
            
            # If it's a list of movies, format it nicely
            elif movies:
                # Re-parse for display (extract year from original output)
                pattern = r'([^(]+)\s*\((\d{4})\)'
                matches = re.findall(pattern, tool_outputs[-1])
                movie_list = [f"{title.strip()} ({year})" for title, year in matches]
                answer = f"Here are some movies that match your query:\n\n" + "\n".join(f"- {m}" for m in movie_list)
        else:
            answer = raw_output.replace("Agent stopped due to max iterations.", "").strip()
            if not answer:
                answer = "I found some results, but couldn't format them properly."
        
        result = {
            "answer": answer,
            "movies": movies,
            "tools_used": tools_used,
            "confidence": 0.8 if movies or quiz_data else 0.5,
        }
        
        # Include quiz_data separately so service can use it directly
        if quiz_data:
            result["quiz_data"] = quiz_data
        
        return result
        
    def run(self, user_query: str, chat_history: str = "") -> Dict[str, Any]:
        """
        Executes a single tool call and returns structured output with latency tracking.
        
        Uses LangChain callbacks to capture precise tool execution time.
        
        :param user_query: User's query message
        :param chat_history: Optional chat history string for context
        """
        if not self.executor:
            raise RuntimeError("Agent executor not initialized.")

        # Create callback handler for tool latency tracking
        tool_callback = ToolLatencyCallback()
        
        llm_start = time()
        
        executor_input = {
            "input": user_query,
            "chat_history": chat_history or ""
        }
        
        config = {"callbacks": [tool_callback]}
        
        try:
            result_dict = self.executor.invoke(
                executor_input,
                config=config
            )
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Agent executor error: {str(e)}", exc_info=True)
            
            return {
                "answer": f"I encountered an error while processing your request: {str(e)}. Please try rephrasing your query.",
                "movies": [],
                "tools_used": [],
                "llm_latency_ms": int((time() - llm_start) * 1000),
                "tool_latency_ms": 0,
                "confidence": 0.0,
            }
        
        llm_latency_ms = int((time() - llm_start) * 1000)
        tool_latency_ms = tool_callback.get_total_tool_latency_ms()
        pure_llm_latency_ms = max(0, llm_latency_ms - tool_latency_ms)

        raw_output = result_dict.get("output", str(result_dict))
        intermediate_steps = result_dict.get("intermediate_steps", [])
        
        if self._verbose or ("poster" in user_query.lower() or "image" in user_query.lower()):
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"Agent raw output (first 2000 chars): {str(raw_output)[:2000]}")
            if intermediate_steps:
                logger.info(f"Agent intermediate steps count: {len(intermediate_steps)}")
                for i, step in enumerate(intermediate_steps[-3:]):
                    logger.info(f"Step {i+1}: {str(step)[:500]}")
        
        # If agent stopped due to max_iterations and we have tool output, format it
        if "stopped due to max iterations" in str(raw_output).lower() and intermediate_steps:
            parsed = self._extract_tool_output(intermediate_steps, raw_output)
        else:
            parsed = AgentOutputParser.parse(raw_output)
        parsed["llm_latency_ms"] = pure_llm_latency_ms
        parsed["tool_latency_ms"] = tool_latency_ms
        
        return parsed