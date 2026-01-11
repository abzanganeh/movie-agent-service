from typing import Any, List, Optional
import json
import logging
from pydantic import BaseModel, Field
from langchain.tools import BaseTool
from langchain_core.documents import Document

from .retriever_tool import RetrieverTool
from .question_generators import QuestionGeneratorFactory

logger = logging.getLogger(__name__)


class GenerateQuizArgs(BaseModel):
    topic: str = Field(description="Topic for the quiz (e.g., 'movies' or a specific movie title)")
    num_questions: int = Field(default=10, ge=1, le=10, description="Number of quiz questions to generate (1-10, default 10)")
    quiz_type: str = Field(default="year", description="Type of quiz: 'year', 'director', or 'cast'")


class GenerateMovieQuizTool(BaseTool):
    """
    Generates simple movie quiz questions from retriever metadata.
    Keeps logic deterministic (no LLM) for predictable tool output.
    """

    name: str = "generate_movie_quiz"
    description: str = (
        "Generates movie quiz questions. Use when user wants to play a quiz or trivia game. "
        "Parameters: topic (string), num_questions (integer 1-10, default 10), quiz_type (string: 'year', 'director', or 'cast', default 'year'). "
        "Generate 10 questions per quiz session by default. Questions will be shown one at a time with feedback after each answer. "
        "Quiz types: 'year' (release year), 'director' (who directed), 'cast' (who starred in)."
    )
    retriever: Any = Field(default=None)
    top_k: int = Field(default=5)

    args_schema: type[BaseModel] = GenerateQuizArgs

    def __init__(self, retriever: RetrieverTool, top_k: int = 5, **kwargs):
        super().__init__(**kwargs)
        self.retriever = retriever
        self.top_k = int(top_k)

    def _run(self, topic: str, num_questions: int = 1, quiz_type: str = "year", exclude_question_ids: Optional[List[int]] = None) -> str:
        """
        Generate quiz questions using Strategy Pattern (OOP).
        
        Uses QuestionGeneratorFactory to select appropriate generator based on quiz_type.
        Supports: 'year', 'director', 'cast'
        
        :param topic: Topic for the quiz
        :param num_questions: Number of questions to generate
        :param quiz_type: Type of quiz ('year', 'director', 'cast')
        :param exclude_question_ids: Optional list of question IDs to exclude
        :return: JSON string with quiz data
        """
        import random
        
        exclude_question_ids = exclude_question_ids or []
        
        # OOP: Strategy Pattern - get appropriate generator
        generator = QuestionGeneratorFactory.create(quiz_type)
        
        # Retrieve more docs to have options for distractors and randomization
        retrieve_count = min(self.top_k * 3, num_questions * 5)
        docs: List[Document] = self.retriever.retrieve(topic, k=retrieve_count)
        if not docs:
            return json.dumps(
                {"topic": topic, "questions": [], "quiz_type": quiz_type, "note": "No quiz data available."}
            )

        # Randomize document order to get different questions each time
        docs_shuffled = list(docs)
        random.shuffle(docs_shuffled)

        questions = []
        question_id = 1
        skipped_count = 0
        max_skips = retrieve_count  # Don't skip more than total docs retrieved
        
        for doc in docs_shuffled:
            if len(questions) >= num_questions:
                break

            # Skip if this question was already asked
            if exclude_question_ids and question_id in exclude_question_ids:
                question_id += 1
                continue

            # OOP: Delegate question generation to appropriate generator
            question = generator.generate_question(doc, question_id, docs_shuffled)
            
            if question:
                questions.append(question)
                question_id += 1
            else:
                skipped_count += 1
                # If we've skipped too many, break to avoid infinite loop
                if skipped_count >= max_skips:
                    logger.warning(f"CastQuestionGenerator: Skipped {skipped_count} documents without cast data. Only found {len(questions)} questions.")
                    break

        # If no questions generated, return helpful error based on quiz type
        if not questions:
            if quiz_type == "cast":
                return json.dumps({
                    "topic": topic,
                    "quiz_type": quiz_type,
                    "questions": [],
                    "error": "No cast/actor data available in the movie database. Please try 'year' or 'director' quiz types instead.",
                    "note": "Cast quiz requires actor/cast information in movie metadata, which may not be available for all movies."
                })
            elif quiz_type == "director":
                return json.dumps({
                    "topic": topic,
                    "quiz_type": quiz_type,
                    "questions": [],
                    "error": "No director data available in the movie database. Please try 'year' quiz type instead.",
                    "note": "Director quiz requires director information in movie metadata, which may not be available for all movies."
                })
            else:
                # Year quiz should always work, but handle edge case
                return json.dumps({
                    "topic": topic,
                    "quiz_type": quiz_type,
                    "questions": [],
                    "error": "No quiz questions could be generated. Please try again or specify a different topic.",
                    "note": "Unable to generate questions from available movie data."
                })
        
        return json.dumps({
            "topic": topic,
            "quiz_type": quiz_type,
            "questions": questions
        })

    async def _arun(self, topic: str, num_questions: int = 10, quiz_type: str = "year") -> str:
        return self._run(topic, num_questions=num_questions, quiz_type=quiz_type)


class CheckQuizAnswerArgs(BaseModel):
    question: str
    user_answer: str
    correct_answer: str


class CheckQuizAnswerTool(BaseTool):
    """
    Checks a quiz answer. Simple equality check for determinism.
    """

    name: str = "check_quiz_answer"
    description: str = (
        "ONLY use this tool when the user is explicitly answering a quiz question that was previously generated. "
        "Input: question, user_answer, correct_answer. "
        "DO NOT use this for general feedback, corrections, or non-quiz responses. "
        "Returns JSON with correctness and feedback."
    )

    args_schema: type[BaseModel] = CheckQuizAnswerArgs

    def _run(self, question: str, user_answer: str, correct_answer: str) -> str:
        correct = user_answer.strip().lower() == correct_answer.strip().lower()
        return json.dumps(
            {
                "question": question,
                "user_answer": user_answer,
                "correct_answer": correct_answer,
                "is_correct": correct,
                "feedback": "Correct!" if correct else "Incorrect. Try again.",
            }
        )

    async def _arun(self, question: str, user_answer: str, correct_answer: str) -> str:
        return self._run(question, user_answer, correct_answer)


class CompareMoviesArgs(BaseModel):
    movie_a: str
    movie_b: str
    aspects: Optional[List[str]] = Field(
        default=None,
        description="Optional list of aspects to compare (e.g., year, genre, director).",
    )


class CompareMoviesTool(BaseTool):
    """
    Compares two movies using retriever metadata (deterministic).
    """

    name: str = "compare_movies"
    description: str = (
        "Compare two movies on metadata including year, genres, director, and IMDb rating. "
        "Always include ratings in the comparison to help users understand which movie is better rated."
    )
    retriever: Any = Field(default=None)
    top_k: int = Field(default=3)

    args_schema: type[BaseModel] = CompareMoviesArgs

    def __init__(self, retriever: RetrieverTool, top_k: int = 3, **kwargs):
        super().__init__(**kwargs)
        self.retriever = retriever
        self.top_k = int(top_k)

    def _run(self, movie_a: str, movie_b: str, aspects: Optional[List[str]] = None) -> str:
        a_doc = self._first_doc(movie_a)
        b_doc = self._first_doc(movie_b)

        def meta_summary(doc: Optional[Document]) -> dict:
            if not doc:
                return {"title": "Unknown", "year": "Unknown", "genres": [], "director": "Unknown", "rating": None}
            meta = getattr(doc, "metadata", {}) or {}
            return {
                "title": meta.get("title", "Unknown"),
                "year": meta.get("year", "Unknown"),
                "genres": meta.get("genres", meta.get("genre", [])),
                "director": meta.get("director", "Unknown"),
                "rating": meta.get("rating", None),  # IMDb rating
            }

        a_meta = meta_summary(a_doc)
        b_meta = meta_summary(b_doc)

        # Always include rating in comparison (OOP: Encapsulation - rating is part of movie comparison)
        aspects = aspects or ["title", "year", "genres", "director", "rating"]
        # Ensure rating is always included even if not in aspects list
        if "rating" not in aspects:
            aspects.append("rating")
        comparison = {aspect: {"a": a_meta.get(aspect), "b": b_meta.get(aspect)} for aspect in aspects}

        return json.dumps(
            {
                "movie_a": a_meta,
                "movie_b": b_meta,
                "comparison": comparison,
            }
        )

    async def _arun(
        self, movie_a: str, movie_b: str, aspects: Optional[List[str]] = None
    ) -> str:
        return self._run(movie_a, movie_b, aspects=aspects)

    def _first_doc(self, query: str) -> Optional[Document]:
        try:
            docs = self.retriever.retrieve(query, k=self.top_k)
            return docs[0] if docs else None
        except Exception:
            return None

