"""
Test script for poster analysis functionality.

Tests title extraction and mood inference for multiple movies.
"""

import sys
from pathlib import Path

# Add service to path
service_dir = Path(__file__).parent
sys.path.insert(0, str(service_dir / "src"))

from movie_agent.app import MovieAgentApp
from movie_agent.config import MovieAgentConfig
import os


def test_poster_analysis(image_path: str, expected_title: str, expected_mood: str):
    """
    Test poster analysis for a single movie.
    
    :param image_path: Path to poster image
    :param expected_title: Expected movie title
    :param expected_mood: Expected mood (e.g., "Comedic", "Thrilling")
    """
    print(f"\n{'='*60}")
    print(f"Testing: {expected_title}")
    print(f"{'='*60}")
    
    # Initialize app
    config = MovieAgentConfig(
        llm_provider="groq",
        llm_model="llama-3.1-8b-instant",
        enable_vision=True,
        enable_memory=False,
        warmup_on_start=False,
        verbose=True,
    )
    
    app = MovieAgentApp(config)
    app.initialize()
    
    # Analyze poster
    try:
        result = app.analyze_poster(image_path)
        
        print(f"Expected Title: {expected_title}")
        print(f"Actual Title:   {result.title}")
        print(f"Expected Mood:  {expected_mood}")
        print(f"Actual Mood:    {result.mood}")
        print(f"Confidence:     {result.confidence}")
        print(f"Caption:        {result.caption}")
        
        # Validation
        title_match = result.title and expected_title.lower() in result.title.lower()
        mood_match = result.mood == expected_mood
        
        if title_match and mood_match:
            print("✅ PASS")
            return True
        else:
            print("❌ FAIL")
            if not title_match:
                print(f"   Title mismatch: expected '{expected_title}', got '{result.title}'")
            if not mood_match:
                print(f"   Mood mismatch: expected '{expected_mood}', got '{result.mood}'")
            return False
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # Test cases - update paths as needed
    test_cases = [
        # ("path/to/poster.png", "Expected Title", "Expected Mood"),
        # Add your test cases here
    ]
    
    if not test_cases:
        print("No test cases configured. Update test_cases list with poster paths.")
        sys.exit(0)
    
    results = []
    for image_path, expected_title, expected_mood in test_cases:
        if os.path.exists(image_path):
            passed = test_poster_analysis(image_path, expected_title, expected_mood)
            results.append(passed)
        else:
            print(f"⚠️  Skipping {image_path} - file not found")
    
    print(f"\n{'='*60}")
    print(f"Results: {sum(results)}/{len(results)} passed")
    print(f"{'='*60}")



