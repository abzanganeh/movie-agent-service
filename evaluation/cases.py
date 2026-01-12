EVAL_CASES = [
    {
        "id": "known_fact_director",
        "question": "Who directed Inception?",
        "should_refuse": False,
        "expected_movies": ["Inception"],
    },
    {
        "id": "ambiguous_best_movie",
        "question": "What is the best movie ever made?",
        "should_refuse": True,
        "expected_movies": [],
    },
    {
        "id": "nonexistent_movie",
        "question": "Who directed Blue Quantum Banana?",
        "should_refuse": True,
        "expected_movies": [],
    },
]
