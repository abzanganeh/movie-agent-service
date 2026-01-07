"""
Question Generators for Quiz System - Strategy Pattern Implementation

OOP Principles:
- Single Responsibility: Each generator handles one question type
- Open/Closed: Easy to add new generators without modifying existing code
- Dependency Inversion: Abstract base class defines interface
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import random
import re
import logging
from langchain_core.documents import Document


class QuestionGenerator(ABC):
    """
    Abstract base class for question generators.
    
    OOP: Strategy Pattern - defines interface for question generation.
    Each concrete generator implements one quiz type.
    """
    
    @abstractmethod
    def generate_question(self, doc: Document, question_id: int, all_docs: List[Document]) -> Optional[Dict[str, Any]]:
        """
        Generate a quiz question from a document.
        
        :param doc: Document to generate question from
        :param question_id: Unique ID for this question
        :param all_docs: All available documents (for generating distractors)
        :return: Question dict with id, question, options, answer, or None if invalid
        """
        pass
    
    @abstractmethod
    def get_quiz_type(self) -> str:
        """Get the quiz type this generator handles (e.g., 'year', 'director', 'cast')."""
        pass
    
    def _get_metadata(self, doc: Document) -> Dict[str, Any]:
        """Helper to extract metadata from document."""
        return getattr(doc, "metadata", {}) or {}
    
    def _escape_title(self, title: str) -> str:
        """Escape quotes in title to prevent JSON issues."""
        return title.replace('"', '\\"').replace("'", "\\'")
    
    def _shuffle_options(self, options: List[str], correct_answer: str) -> List[str]:
        """
        Shuffle options while ensuring correct answer is included.
        
        :param options: List of option strings
        :param correct_answer: The correct answer (must be in options)
        :return: Shuffled list of options
        """
        # Ensure correct answer is in options
        if correct_answer not in options:
            if len(options) < 3:
                options.append(correct_answer)
            else:
                options[-1] = correct_answer
        
        # Shuffle to randomize order
        shuffled = list(options)
        random.shuffle(shuffled)
        return shuffled


class YearQuestionGenerator(QuestionGenerator):
    """
    Generates year-based quiz questions.
    
    Question format: "What year was '{title}' released?"
    """
    
    def get_quiz_type(self) -> str:
        return "year"
    
    def generate_question(self, doc: Document, question_id: int, all_docs: List[Document]) -> Optional[Dict[str, Any]]:
        """Generate a year-based question."""
        meta = self._get_metadata(doc)
        title = meta.get("title", "Unknown Title")
        year = meta.get("year", "Unknown Year")
        
        # Validate required fields
        if not title or title == "Unknown Title" or not year or year == "Unknown Year":
            return None
        
        correct = str(year)
        
        # Generate distractors (years close to correct answer)
        distractors: List[str] = []
        try:
            y = int(year)
            distractor_offsets = [-1, 1, 2]
            random.shuffle(distractor_offsets)
            distractors = [str(y + offset) for offset in distractor_offsets[:3]]
        except (ValueError, TypeError):
            distractors = ["1999", "2005", "2010"]
        
        # Build options list (correct + distractors, limit to 3)
        options = []
        for opt in [correct] + distractors:
            if opt not in options:
                options.append(opt)
            if len(options) == 3:
                break
        
        # Shuffle options
        options = self._shuffle_options(options, correct)
        
        # Build question
        safe_title = self._escape_title(title)
        return {
            "id": question_id,
            "question": f"What year was \"{safe_title}\" released?",
            "options": options,
            "answer": correct,
        }


class DirectorQuestionGenerator(QuestionGenerator):
    """
    Generates director-based quiz questions.
    
    Question format: "Who directed '{title}'?"
    """
    
    def get_quiz_type(self) -> str:
        return "director"
    
    def generate_question(self, doc: Document, question_id: int, all_docs: List[Document]) -> Optional[Dict[str, Any]]:
        """Generate a director-based question."""
        logger = logging.getLogger(__name__)
        
        meta = self._get_metadata(doc)
        title = meta.get("title", "Unknown Title")
        
        # Try multiple possible field names for director
        director = None
        for field in ["director", "directors", "directed_by", "filmmaker", "director_name"]:
            value = meta.get(field)
            if value:
                if isinstance(value, list):
                    director = value[0] if value else None
                elif isinstance(value, str) and value.strip() and value != "Unknown":
                    director = value.strip()
                if director:
                    break
        
        # Fallback: Extract from page_content if not in metadata (for old vector stores)
        if not director:
            page_content = getattr(doc, "page_content", "") or ""
            # Look for "Director: <name>" pattern in page_content
            director_match = re.search(r'Director:\s*([^\.]+)', page_content, re.IGNORECASE)
            if director_match:
                director = director_match.group(1).strip()
                logger.debug(f"DirectorQuestionGenerator: Extracted director '{director}' from page_content for '{title}'")
        
        # Log available metadata keys for debugging
        if not director:
            available_keys = list(meta.keys())[:10]
            logger.debug(f"DirectorQuestionGenerator: No director found for '{title}'. Available metadata keys (first 10): {available_keys}")
        
        # Validate required fields
        if not title or title == "Unknown Title" or not director:
            return None
        
        correct = str(director).strip()
        
        # Generate distractors from other documents' directors
        distractors: List[str] = []
        director_set = {correct.lower()}
        
        # Collect unique directors from other documents
        for other_doc in all_docs:
            if other_doc == doc:
                continue
            other_meta = self._get_metadata(other_doc)
            # Try multiple field names for director
            other_director = None
            for field in ["director", "directors", "directed_by", "filmmaker", "director_name"]:
                value = other_meta.get(field)
                if value:
                    if isinstance(value, list):
                        other_director = value[0] if value else None
                    elif isinstance(value, str) and value.strip() and value != "Unknown":
                        other_director = value.strip()
                    if other_director:
                        break
            
            # Fallback: Extract from page_content if not in metadata
            if not other_director:
                other_page_content = getattr(other_doc, "page_content", "") or ""
                director_match = re.search(r'Director:\s*([^\.]+)', other_page_content, re.IGNORECASE)
                if director_match:
                    other_director = director_match.group(1).strip()
            
            if other_director and other_director != "Unknown":
                other_director_lower = str(other_director).strip().lower()
                if other_director_lower not in director_set:
                    distractors.append(str(other_director).strip())
                    director_set.add(other_director_lower)
                if len(distractors) >= 3:
                    break
        
        # If not enough distractors, add generic ones
        while len(distractors) < 3:
            generic_directors = ["Steven Spielberg", "Christopher Nolan", "Martin Scorsese", "Quentin Tarantino"]
            for gd in generic_directors:
                if gd.lower() not in director_set:
                    distractors.append(gd)
                    director_set.add(gd.lower())
                    if len(distractors) >= 3:
                        break
            if len(distractors) >= 3:
                break
        
        # Build options list (correct + distractors, limit to 3)
        options = []
        for opt in [correct] + distractors[:3]:
            if opt not in options:
                options.append(opt)
            if len(options) == 3:
                break
        
        # Shuffle options
        options = self._shuffle_options(options, correct)
        
        # Build question
        safe_title = self._escape_title(title)
        return {
            "id": question_id,
            "question": f"Who directed \"{safe_title}\"?",
            "options": options,
            "answer": correct,
        }


class CastQuestionGenerator(QuestionGenerator):
    """
    Generates cast/actor-based quiz questions.
    
    Question format: "Who starred in '{title}'?" or "Which actor appeared in '{title}'?"
    """
    
    def get_quiz_type(self) -> str:
        return "cast"
    
    def _extract_actors(self, meta: Dict[str, Any], page_content: str = "") -> List[str]:
        """Extract actor names from metadata (supports multiple field names)."""
        logger = logging.getLogger(__name__)
        
        # Try different possible field names (expanded list)
        # Note: Movie model uses "stars" field (from CSV "Star Cast" column)
        actors = []
        field_names = [
            "stars",  # Primary field from Movie model (from CSV "Star Cast")
            "cast", "actors", "actor", "starring", 
            "cast_members", "main_cast", "lead_actors", "principal_cast",
            "cast_list", "actors_list", "starring_cast", "star_cast"
        ]
        
        for field in field_names:
            value = meta.get(field)
            if value:
                if isinstance(value, list):
                    actors.extend([str(a).strip() for a in value if a and str(a).strip() and str(a).strip() != "Unknown"])
                elif isinstance(value, str):
                    # Handle comma-separated string
                    actors.extend([a.strip() for a in value.split(",") if a.strip() and a.strip() != "Unknown"])
                if actors:  # If we found actors, stop searching
                    break
        
        # Fallback: Extract from page_content if not in metadata (for old vector stores)
        if not actors and page_content:
            # Look for "Stars: <list>" pattern in page_content
            # Match "Stars: " followed by text until next field (period + space + capital letter or end)
            stars_match = re.search(r'Stars:\s*([^\.]+?)(?=\.\s+[A-Z]|\.$)', page_content, re.IGNORECASE)
            if stars_match:
                stars_text = stars_match.group(1).strip()
                # Parse: try comma-separated first, then handle concatenated names
                if "," in stars_text:
                    actors = [a.strip() for a in stars_text.split(",") if a.strip()]
                else:
                    # Handle concatenated names (split on capital after lowercase/digit)
                    actors = [a.strip() for a in re.split(r'(?<=[a-z0-9])(?=[A-Z])', stars_text) if a.strip()]
                logger.info(f"CastQuestionGenerator: Extracted {len(actors)} actors from page_content: {actors[:3]}...")
                logger.debug(f"CastQuestionGenerator: Full page_content excerpt: {page_content[:200]}")
        
        # Log if no actors found (for debugging) - show first few keys
        if not actors:
            available_keys = list(meta.keys())[:10]  # Show first 10 keys
            logger.debug(f"CastQuestionGenerator: No cast found. Available metadata keys (first 10): {available_keys}")
            # Also log the actual values for stars/cast fields if they exist
            for field in ["stars", "cast", "actors"]:
                if field in meta:
                    logger.debug(f"CastQuestionGenerator: Field '{field}' exists but value is: {meta[field]}")
        
        return [a for a in actors if a and a != "Unknown"]
    
    def generate_question(self, doc: Document, question_id: int, all_docs: List[Document]) -> Optional[Dict[str, Any]]:
        """Generate a cast/actor-based question."""
        logger = logging.getLogger(__name__)
        
        meta = self._get_metadata(doc)
        title = meta.get("title", "Unknown Title")
        page_content = getattr(doc, "page_content", "") or ""
        actors = self._extract_actors(meta, page_content)
        
        # Validate required fields
        if not title or title == "Unknown Title":
            return None
        
        # Log missing cast data for debugging
        if not actors:
            logger.debug(f"CastQuestionGenerator: No cast data found for '{title}'. Available metadata keys: {list(meta.keys())}")
            return None
        
        # Debug: Log what actors were extracted
        logger.info(f"CastQuestionGenerator: Extracted {len(actors)} actors for '{title}': {actors[:3]}...")
        
        # Pick a random actor from the cast as the correct answer
        correct = random.choice(actors)
        
        # Generate distractors from other documents' casts
        distractors: List[str] = []
        actor_set = {correct.lower()}
        
        # Collect unique actors from other documents
        for other_doc in all_docs:
            if other_doc == doc:
                continue
            other_meta = self._get_metadata(other_doc)
            other_page_content = getattr(other_doc, "page_content", "") or ""
            other_actors = self._extract_actors(other_meta, other_page_content)
            for actor in other_actors:
                actor_lower = actor.lower()
                if actor_lower not in actor_set:
                    distractors.append(actor)
                    actor_set.add(actor_lower)
                if len(distractors) >= 3:
                    break
            if len(distractors) >= 3:
                break
        
        # If not enough distractors, add generic ones
        while len(distractors) < 3:
            generic_actors = ["Tom Hanks", "Meryl Streep", "Leonardo DiCaprio", "Scarlett Johansson"]
            for ga in generic_actors:
                if ga.lower() not in actor_set:
                    distractors.append(ga)
                    actor_set.add(ga.lower())
                    if len(distractors) >= 3:
                        break
            if len(distractors) >= 3:
                break
        
        # Build options list (correct + distractors, limit to 3)
        options = []
        for opt in [correct] + distractors[:3]:
            if opt not in options:
                options.append(opt)
            if len(options) == 3:
                break
        
        # Shuffle options
        options = self._shuffle_options(options, correct)
        
        # Build question
        safe_title = self._escape_title(title)
        return {
            "id": question_id,
            "question": f"Who starred in \"{safe_title}\"?",
            "options": options,
            "answer": correct,
        }


class QuestionGeneratorFactory:
    """
    Factory for creating question generators.
    
    OOP: Factory Pattern - centralizes generator creation logic.
    """
    
    _generators: Dict[str, QuestionGenerator] = {
        "year": YearQuestionGenerator(),
        "director": DirectorQuestionGenerator(),
        "cast": CastQuestionGenerator(),
    }
    
    @classmethod
    def create(cls, quiz_type: str) -> QuestionGenerator:
        """
        Create a question generator for the specified quiz type.
        
        :param quiz_type: Type of quiz ('year', 'director', 'cast')
        :return: QuestionGenerator instance
        :raises ValueError: If quiz_type is not supported
        """
        quiz_type_lower = quiz_type.lower().strip()
        generator = cls._generators.get(quiz_type_lower)
        
        if not generator:
            # Default to year if unknown type
            return cls._generators["year"]
        
        return generator
    
    @classmethod
    def get_supported_types(cls) -> List[str]:
        """Get list of supported quiz types."""
        return list(cls._generators.keys())
    
    @classmethod
    def register(cls, quiz_type: str, generator: QuestionGenerator) -> None:
        """
        Register a new question generator.
        
        OOP: Open/Closed Principle - allows extension without modification.
        
        :param quiz_type: Type identifier
        :param generator: QuestionGenerator instance
        """
        cls._generators[quiz_type.lower()] = generator

