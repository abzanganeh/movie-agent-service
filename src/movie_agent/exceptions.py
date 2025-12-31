class MovieAgentError(Exception):
    """Base exception for movie agent service."""


class AgentNotInitializedError(MovieAgentError):
    """Raised when agent is used before initialization."""


class VisionAnalystNotInitializedError(MovieAgentError):
    """Raised when vision analyst is used before initialization."""