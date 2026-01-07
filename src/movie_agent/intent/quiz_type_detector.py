"""
Quiz Type Detector - Detects quiz type from user input.

OOP: Single Responsibility - only handles quiz type detection and prompting.
"""
import re
from typing import Optional


def detect_quiz_type(user_input: str) -> Optional[str]:
    """
    Detect quiz type from user input using keyword matching.
    
    OOP: Single Responsibility - only handles quiz type detection.
    
    Checks for keywords related to:
    - Cast/actors: "cast", "actor", "star", "starring"
    - Director: "director", "directed", "helmed"
    - Year: "year", "released", "when"
    
    :param user_input: User's input text
    :return: Quiz type ('cast', 'director', 'year') or None if not detected
    """
    text = user_input.lower().strip()
    
    # Cast/actor keywords (highest priority - most specific)
    cast_patterns = [
        r'\b(cast|actor|actors|star|stars|starring|who stars? in|who played|who acted|performed by)\b',
        r'\b(cast|actor|star)\s+(quiz|trivia|game|questions?)\b',
    ]
    if any(re.search(pattern, text) for pattern in cast_patterns):
        return "cast"
    
    # Director keywords
    director_patterns = [
        r'\b(director|directed|who directed|helmed|who helmed|filmmaker)\b',
        r'\b(director|directed)\s+(quiz|trivia|game|questions?)\b',
    ]
    if any(re.search(pattern, text) for pattern in director_patterns):
        return "director"
    
    # Year keywords
    year_patterns = [
        r'\b(year|years|released|when was|release date|what year|from what year)\b',
        r'\b(year|released)\s+(quiz|trivia|game|questions?)\b',
    ]
    if any(re.search(pattern, text) for pattern in year_patterns):
        return "year"
    
    # No specific type detected
    return None


def get_quiz_type_prompt(quiz_type: Optional[str] = None) -> str:
    """
    Get a user-friendly prompt suggesting quiz types.
    
    OOP: Single Responsibility - only handles quiz type prompting logic.
    
    :param quiz_type: Current quiz type (if any)
    :return: Prompt string
    """
    if quiz_type:
        type_names = {
            "cast": "cast/actor",
            "director": "director",
            "year": "year",
        }
        return f"Continuing with {type_names.get(quiz_type, 'quiz')} questions."
    
    # OOP: Encapsulation - prompt message is defined here, not in service layer
    return (
        "What type of quiz would you like to play?\n\n"
        "• **Year** - Questions about movie release years\n"
        "• **Director** - Questions about who directed movies\n"
        "• **Cast** - Questions about actors who starred in movies\n\n"
        "Please specify: 'year', 'director', or 'cast'"
    )


def get_available_quiz_types_message(failed_type: Optional[str] = None) -> str:
    """
    Get a message listing available quiz types, optionally excluding a failed type.
    
    OOP: Single Responsibility - handles quiz type availability messaging.
    
    :param failed_type: Quiz type that failed (to exclude from suggestions)
    :return: Message string with available quiz types
    """
    available_types = []
    
    if failed_type != "year":
        available_types.append("• **Year** - Questions about release years")
    
    if failed_type != "director":
        available_types.append("• **Director** - Questions about directors")
    
    if failed_type != "cast":
        available_types.append("• **Cast** - Questions about actors")
    
    if not available_types:
        return "No quiz types are currently available."
    
    return "💡 **Available quiz types:**\n" + "\n".join(available_types)
