import ast
from typing import Dict, Any


class AgentOutputParser:
    @staticmethod
    def parse(text: str) -> Dict[str, Any]:
        """
        Parses the agent's final output into structured fields.
        """
        if "METADATA:" not in text:
            return {
                "answer": text.strip(),
                "movies": [],
                "confidence": None,
                "tools_used": [],
            }

        answer_part, metadata_part = text.split("METADATA:", 1)

        metadata = {}
        for line in metadata_part.strip().splitlines():
            if ":" not in line:
                continue

            key, value = line.split(":", 1)
            key = key.strip("- ").strip()

            try:
                metadata[key] = ast.literal_eval(value.strip())
            except Exception:
                metadata[key] = value.strip()

        # Normalize tools_used to always be a list
        tools_used_raw = metadata.get("tools_used", [])
        if isinstance(tools_used_raw, str):
            # Try to parse string representation of list
            try:
                tools_used = ast.literal_eval(tools_used_raw)
                if not isinstance(tools_used, list):
                    tools_used = [tools_used_raw]
            except Exception:
                tools_used = [tools_used_raw] if tools_used_raw else []
        elif isinstance(tools_used_raw, list):
            tools_used = tools_used_raw
        else:
            tools_used = []

        # Normalize movies to always be a list
        movies_raw = metadata.get("movies", [])
        if isinstance(movies_raw, str):
            try:
                movies = ast.literal_eval(movies_raw)
                if not isinstance(movies, list):
                    movies = []
            except Exception:
                # If parsing fails, treat as empty list (safe default)
                movies = []
        elif isinstance(movies_raw, list):
            movies = movies_raw
        else:
            movies = []

        return {
            "answer": answer_part.replace("FINAL ANSWER:", "").strip(),
            "movies": movies,
            "confidence": metadata.get("confidence"),
            "tools_used": tools_used,
        }
