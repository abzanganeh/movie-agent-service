import ast
from typing import Dict, Any


class AgentOutputParser:
    @staticmethod
    def parse(text: str) -> Dict[str, Any]:
        """
        Parses the agent's final output into structured fields.
        """
        # Clean up any tool call syntax that might have leaked into the output
        # Remove function tags like <function=...>...</function>
        import re
        # Remove various tool call syntax patterns (more aggressive)
        # Pattern: <function=tool_name>{...}</function>
        text = re.sub(r'<function=[^>]+>\s*\{[^}]*\}\s*</function>', '', text, flags=re.DOTALL)
        text = re.sub(r'<function=[^>]+>.*?</function>', '', text, flags=re.DOTALL)
        text = re.sub(r'<function=[^>]+>', '', text)
        text = re.sub(r'</function>', '', text)
        # Remove tool_name{...} patterns (e.g., "movie_search{"query": "..."}")
        text = re.sub(r'\b\w+\s*\{[^}]*\}', '', text)
        # Remove standalone tool names that appear before answers
        text = re.sub(r'^(movie_search|generate_movie_quiz|check_quiz_answer|compare_movies|search_actor|search_director|search_year)\s*', '', text, flags=re.MULTILINE)
        
        if "METADATA:" not in text:
            # Clean up any remaining tool syntax
            text = text.strip()
            return {
                "answer": text,
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
                # Try to parse as Python literal (handles None, lists, numbers, etc.)
                parsed_value = ast.literal_eval(value.strip())
                metadata[key] = parsed_value
            except (ValueError, SyntaxError):
                # If parsing fails, treat as string (strip quotes if present)
                value_str = value.strip()
                # Remove surrounding quotes if present
                if (value_str.startswith('"') and value_str.endswith('"')) or \
                   (value_str.startswith("'") and value_str.endswith("'")):
                    value_str = value_str[1:-1]
                metadata[key] = value_str

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

        # Extract poster-specific fields (may be None if not poster analysis)
        title = metadata.get("title")
        mood = metadata.get("mood")
        caption = metadata.get("caption")
        
        # Normalize title (can be None, string, or "null")
        if title == "null" or title == "None" or title is None:
            title = None
        elif isinstance(title, str):
            title = title.strip() if title.strip() else None
        
        # Clean the answer part - remove any remaining tool syntax
        answer_clean = answer_part.replace("FINAL ANSWER:", "").strip()
        # Remove any tool call patterns that might have leaked (e.g., "movie_search{"query": "..."}")
        import re
        answer_clean = re.sub(r'\b\w+\s*\{[^}]*\}', '', answer_clean)
        # Remove standalone tool names that appear before answers
        tool_names = ['movie_search', 'generate_movie_quiz', 'check_quiz_answer', 'compare_movies', 
                     'search_actor', 'search_director', 'search_year', 'analyze_movie_poster']
        for tool_name in tool_names:
            # Remove tool name at start of line or after newline
            answer_clean = re.sub(rf'^({tool_name})\s*', '', answer_clean, flags=re.MULTILINE)
            answer_clean = re.sub(rf'\n({tool_name})\s*', '\n', answer_clean, flags=re.MULTILINE)
        answer_clean = answer_clean.strip()
        
        return {
            "answer": answer_clean,
            "movies": movies,
            "confidence": metadata.get("confidence"),
            "tools_used": tools_used,
            "title": title,  # Poster analysis: identified movie title
            "mood": mood,    # Poster analysis: synthesized mood
            "caption": caption,  # Poster analysis: vision tool caption
        }
