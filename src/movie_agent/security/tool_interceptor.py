"""
Tool call interceptor for security validation.

OOP: Single Responsibility - Only handles tool call validation.
"""

from typing import Any, Dict
import logging

from .tool_policy import ToolPolicy
from .input_validator import InputValidator
from .exceptions import ToolPolicyViolationError, ValidationError
from ..intent.agent_intent import AgentIntent

logger = logging.getLogger(__name__)


class ToolCallInterceptor:
    """
    Intercepts and validates tool calls before execution.
    
    Validates:
    - Tool is allowed for given intent and context
    - Tool parameters are valid and sanitized
    """

    @staticmethod
    def validate_tool_call(
        tool_name: str,
        tool_params: Dict[str, Any],
        intent: AgentIntent,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Validate tool call before execution.
        
        :param tool_name: Name of the tool being called
        :param tool_params: Parameters for the tool
        :param intent: User's detected intent
        :param context: Context dictionary (quiz_active, has_poster, etc.)
        :return: Validated and sanitized parameters
        :raises ToolPolicyViolationError: If tool is not allowed
        :raises ValidationError: If parameters are invalid
        """
        if context is None:
            context = {}

        # Check tool is allowed for this intent
        try:
            ToolPolicy.validate_tool_call(tool_name, intent, context)
        except ToolPolicyViolationError as e:
            logger.warning(
                f"Tool policy violation: {tool_name} not allowed for intent {intent.value}. "
                f"Context: {context}"
            )
            raise

        # Validate and sanitize parameters
        try:
            validated_params = InputValidator.validate_tool_parameters(tool_name, tool_params)
        except ValidationError as e:
            logger.warning(
                f"Parameter validation failed for tool {tool_name}: {str(e)}. "
                f"Params: {tool_params}"
            )
            raise

        logger.debug(f"Tool call validated: {tool_name} with params {validated_params}")
        return validated_params

