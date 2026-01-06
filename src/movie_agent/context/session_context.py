"""
Session context domain objects.

Pure domain models - no Flask, no LangChain, no agent logic.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class PosterContext:
    """Poster analysis context."""
    caption: str
    title: Optional[str]
    mood: str
    confidence: float
    inferred_genres: list[str]

    def has_title(self) -> bool:
        """Check if title was identified."""
        return self.title is not None and self.title.strip() != ""


@dataclass
class SessionContext:
    """Session context - single source of truth for session state."""
    poster: Optional[PosterContext] = None

    def has_poster(self) -> bool:
        """Check if poster context exists."""
        return self.poster is not None

    def clear_poster(self) -> None:
        """Clear poster context."""
        self.poster = None


