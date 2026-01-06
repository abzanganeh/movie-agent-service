"""
Intent classification for agent behavior.

Provides formal intent taxonomy for explicit, testable intent routing.
Includes deterministic intent detection function for production-safe routing.
"""
from .agent_intent import AgentIntent, detect_intent

__all__ = ["AgentIntent", "detect_intent"]

