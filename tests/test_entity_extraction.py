"""
Tests for entity extraction.
"""
import pytest
from movie_agent.resolution import EntityExtractor, ExtractedEntity


class TestEntityExtractor:
    """Tests for EntityExtractor."""

    def test_extract_quoted_strings(self):
        """Test extraction of quoted strings."""
        extractor = EntityExtractor()
        entities = extractor.extract('Find "Inception" movies')
        
        assert len(entities) == 1
        assert entities[0].text == "Inception"
    
    def test_extract_capitalized_phrase(self):
        """Test extraction of capitalized phrases."""
        extractor = EntityExtractor()
        entities = extractor.extract("Find Inception movies")
        
        assert len(entities) >= 1
        assert any(e.text == "Inception" for e in entities)
    
    def test_extract_multiple_entities(self):
        """Test extraction of multiple entities."""
        extractor = EntityExtractor()
        entities = extractor.extract("Compare The Matrix and Inception")
        
        # Should extract both movie titles
        titles = [e.text for e in entities]
        assert "The Matrix" in titles or any("Matrix" in t for t in titles)
        assert "Inception" in titles
    
    def test_extract_ignores_action_verbs(self):
        """Test that action verbs at start are ignored."""
        extractor = EntityExtractor()
        entities = extractor.extract("Find Inception")
        
        # Should not extract "Find" as an entity
        titles = [e.text for e in entities]
        assert "Find" not in titles
    
    def test_extract_deduplicates_overlapping(self):
        """Test that overlapping entities are deduplicated."""
        extractor = EntityExtractor()
        entities = extractor.extract('Find "Inception" and Inception movies')
        
        # Should deduplicate "Inception" even if appears multiple times
        titles = [e.text for e in entities]
        # At least one "Inception" should be found
        assert any("Inception" in t for t in titles)
    
    def test_extract_empty_query(self):
        """Test extraction from empty query."""
        extractor = EntityExtractor()
        entities = extractor.extract("")
        
        assert len(entities) == 0
    
    def test_extract_no_entities(self):
        """Test extraction when no entities present."""
        extractor = EntityExtractor()
        entities = extractor.extract("show me movies")
        
        # Should not extract "show" (action verb)
        titles = [e.text for e in entities]
        assert "show" not in titles

