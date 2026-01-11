from typing import Protocol, List
from ..schemas import PosterAnalysisResponse

class VisionTool(Protocol):
    """Protocol for a vision analysis tool used by the agent."""
    def analyze_poster(self, image_path: str) -> PosterAnalysisResponse:
        ...


