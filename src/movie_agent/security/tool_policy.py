"""
Tool whitelist/blacklist policy based on user intent and context.

OOP: Single Responsibility - Only handles tool policy enforcement.
OOP: Open/Closed - Policies are extensible without modifying core code.
"""

from typing import Set, Dict, Any
from ..intent.agent_intent import AgentIntent


class ToolPolicy:
    """
    Defines which tools can be called based on user intent and context.
    
    Prevents unauthorized tool calls by enforcing intent-based restrictions.
    """

    SAFE_TOOLS = {
        "movie_search",
        "get_movie_statistics",
        "search_actor",
        "search_director",
        "search_year",
    }

    RESTRICTED_TOOLS = {
        "generate_movie_quiz",
        "check_quiz_answer",
        "compare_movies",
        "analyze_movie_poster",
    }

    INTENT_TOOL_MAP = {
        AgentIntent.MOVIE_SEARCH: {"movie_search"},
        AgentIntent.MOVIE_COMPARISON: {"compare_movies"},
        AgentIntent.QUIZ_START: {"generate_movie_quiz"},
        AgentIntent.QUIZ_ANSWER: {"check_quiz_answer"},
        AgentIntent.QUIZ_NEXT: set(),
        AgentIntent.ACTOR_LOOKUP: {"search_actor"},
        AgentIntent.DIRECTOR_LOOKUP: {"search_director"},
        AgentIntent.YEAR_LOOKUP: {"search_year"},
        AgentIntent.RATING_LOOKUP: {"get_movie_statistics"},
        AgentIntent.POSTER_QUERY: {"movie_search"},
        AgentIntent.CORRECTION: set(),
        AgentIntent.CHIT_CHAT: set(),
    }

    @staticmethod
    def get_allowed_tools(intent: AgentIntent, context: Dict[str, Any] = None) -> Set[str]:
        """
        Get set of allowed tools for given intent and context.
        
        :param intent: User's detected intent
        :param context: Context dictionary (quiz_active, has_poster, etc.)
        :return: Set of allowed tool names
        """
        if context is None:
            context = {}

        allowed = ToolPolicy.INTENT_TOOL_MAP.get(intent, set()).copy()

        if intent == AgentIntent.QUIZ_ANSWER:
            if not context.get("quiz_active", False):
                allowed.discard("check_quiz_answer")

        if intent == AgentIntent.POSTER_QUERY:
            if not context.get("has_poster", False):
                allowed.discard("movie_search")
                if "analyze_movie_poster" in allowed:
                    allowed.discard("analyze_movie_poster")

        if intent == AgentIntent.MOVIE_COMPARISON:
            if not context.get("has_comparison_context", True):
                allowed.discard("compare_movies")

        return allowed

    @staticmethod
    def is_tool_allowed(tool_name: str, intent: AgentIntent, context: Dict[str, Any] = None) -> bool:
        """
        Check if a tool can be called for given intent and context.
        
        :param tool_name: Name of the tool to check
        :param intent: User's detected intent
        :param context: Context dictionary
        :return: True if tool is allowed, False otherwise
        """
        allowed = ToolPolicy.get_allowed_tools(intent, context)
        return tool_name in allowed

    @staticmethod
    def validate_tool_call(tool_name: str, intent: AgentIntent, context: Dict[str, Any] = None) -> None:
        """
        Validate that a tool call is allowed.
        
        :param tool_name: Name of the tool to check
        :param intent: User's detected intent
        :param context: Context dictionary
        :raises SecurityError: If tool is not allowed
        """
        from .exceptions import ToolPolicyViolationError

        if not ToolPolicy.is_tool_allowed(tool_name, intent, context):
            allowed = ToolPolicy.get_allowed_tools(intent, context)
            raise ToolPolicyViolationError(
                f"Tool '{tool_name}' is not allowed for intent '{intent.value}'. "
                f"Allowed tools: {', '.join(allowed) if allowed else 'none'}"
            )

