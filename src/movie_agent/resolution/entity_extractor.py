"""
Entity extraction for semantic resolution.

Extracts potential movie titles/entities from natural language queries
before resolution.
"""
import re
from typing import List, Set
from dataclasses import dataclass


@dataclass(frozen=True)
class ExtractedEntity:
    """Represents an extracted entity from a query."""
    text: str
    start_pos: int
    end_pos: int


class EntityExtractor:
    """
    Extracts potential movie titles/entities from natural language queries.
    
    Uses heuristics to identify candidate entities:
    - Quoted strings ("Inception")
    - Capitalized phrases (sequences of capitalized words)
    - Common patterns (movie titles often capitalized)
    """
    
    def extract(self, query: str) -> List[ExtractedEntity]:
        """
        Extract potential entities from query.
        
        :param query: Natural language query
        :return: List of ExtractedEntity objects
        """
        entities = []
        
        # Strategy 1: Extract quoted strings
        quoted = self._extract_quoted(query)
        entities.extend(quoted)
        
        # Strategy 2: Extract capitalized phrases (potential titles)
        capitalized = self._extract_capitalized_phrases(query)
        entities.extend(capitalized)
        
        # Remove duplicates (same text, overlapping positions)
        return self._deduplicate_entities(entities)
    
    def _extract_quoted(self, query: str) -> List[ExtractedEntity]:
        """Extract quoted strings (e.g., "Inception")."""
        entities = []
        # Match both single and double quotes
        pattern = r'["\']([^"\']+)["\']'
        
        for match in re.finditer(pattern, query):
            entities.append(ExtractedEntity(
                text=match.group(1),
                start_pos=match.start(),
                end_pos=match.end(),
            ))
        
        return entities
    
    def _extract_capitalized_phrases(self, query: str) -> List[ExtractedEntity]:
        """
        Extract sequences of capitalized words (potential movie titles).
        
        Examples:
        - "Find Inception movies" → ["Inception"]
        - "Compare The Matrix and Inception" → ["The Matrix", "Inception"]
        - "movies like Lord of the Rings" → ["Lord of the Rings"]
        """
        entities = []
        
        # Common action verbs to skip (these often appear at start of queries)
        action_verbs = {"Find", "Compare", "Search", "Show", "List", "Recommend", "Get", "Give"}
        
        # Pattern: sequences of capitalized words, possibly with "the", "of", "a", "an"
        # Minimum 2 characters, allowing articles/prepositions in between
        pattern = r'\b([A-Z][a-z]+(?:\s+(?:the|of|a|an|in|on|at|for|with|from)\s+[A-Z][a-z]+|\s+[A-Z][a-z]+)*)\b'
        
        for match in re.finditer(pattern, query):
            text = match.group(1)
            words = text.split()
            
            # If phrase starts with action verb, try to extract the part after it
            if words[0] in action_verbs and len(words) > 1:
                # Extract part after action verb
                remaining_words = words[1:]
                if remaining_words:
                    # Reconstruct entity from remaining words
                    entity_text = " ".join(remaining_words)
                    # Calculate new position (skip action verb)
                    action_verb_len = len(words[0]) + 1  # +1 for space
                    new_start = match.start() + action_verb_len
                    entities.append(ExtractedEntity(
                        text=entity_text,
                        start_pos=new_start,
                        end_pos=match.end(),
                    ))
                continue
            
            # Skip if single action verb (not a title)
            if len(words) == 1 and words[0] in action_verbs:
                continue
            
            # Filter out common stop phrases that aren't titles
            if self._is_stop_phrase(text):
                continue
            
            # Minimum length check (avoid single common words)
            if len(words) >= 1 and len(text) >= 3:
                entities.append(ExtractedEntity(
                    text=text,
                    start_pos=match.start(),
                    end_pos=match.end(),
                ))
        
        return entities
    
    def _is_stop_phrase(self, text: str) -> bool:
        """Check if text is a common stop phrase (not a movie title)."""
        stop_phrases = {
            "The Matrix",  # This could be a title, but also common phrase
        }
        return text in stop_phrases
    
    def _deduplicate_entities(self, entities: List[ExtractedEntity]) -> List[ExtractedEntity]:
        """
        Remove duplicate entities (same text or overlapping positions).
        
        Prefers entities with longer text (more specific).
        """
        if not entities:
            return []
        
        # Sort by length (descending) and start position
        sorted_entities = sorted(entities, key=lambda e: (-len(e.text), e.start_pos))
        
        seen_texts: Set[str] = set()
        seen_positions: Set[tuple] = set()
        deduplicated = []
        
        for entity in sorted_entities:
            text_lower = entity.text.lower().strip()
            position_range = (entity.start_pos, entity.end_pos)
            
            # Skip if we've seen this exact text
            if text_lower in seen_texts:
                continue
            
            # Skip if position overlaps with existing entity
            if any(self._positions_overlap(position_range, (s, e)) for s, e in seen_positions):
                continue
            
            seen_texts.add(text_lower)
            seen_positions.add(position_range)
            deduplicated.append(entity)
        
        # Sort by position in query (ascending)
        return sorted(deduplicated, key=lambda e: e.start_pos)
    
    def _positions_overlap(self, range1: tuple, range2: tuple) -> bool:
        """Check if two position ranges overlap."""
        start1, end1 = range1
        start2, end2 = range2
        return not (end1 <= start2 or end2 <= start1)

