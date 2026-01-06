"""
Interaction layer for intent routing and query classification.

This layer sits between the UI (CLI/Flask) and the Agent API Facade,
providing deterministic intent classification without LLM calls.
"""
from .intent_types import IntentType
from .intent_router import IntentRouter

__all__ = ["IntentType", "IntentRouter"]

