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

        return {
            "answer": answer_part.replace("FINAL ANSWER:", "").strip(),
            "movies": metadata.get("movies", []),
            "confidence": metadata.get("confidence"),
            "tools_used": metadata.get("tools_used", []),
        }
