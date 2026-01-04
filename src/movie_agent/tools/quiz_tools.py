from typing import Any, List, Optional
import json
from pydantic import BaseModel, Field
from langchain.tools import BaseTool
from langchain_core.documents import Document

from .retriever_tool import RetrieverTool


class GenerateQuizArgs(BaseModel):
    topic: str
    num_questions: int = Field(default=3, ge=1, le=5)


class GenerateMovieQuizTool(BaseTool):
    """
    Generates simple movie quiz questions from retriever metadata.
    Keeps logic deterministic (no LLM) for predictable tool output.
    """

    name: str = "generate_movie_quiz"
    description: str = (
        "Create a short multiple-choice quiz about movies matching the topic. "
        "Returns JSON with questions, options, and answers."
    )
    retriever: Any = Field(default=None)
    top_k: int = Field(default=5)

    args_schema: type[BaseModel] = GenerateQuizArgs

    def __init__(self, retriever: RetrieverTool, top_k: int = 5, **kwargs):
        super().__init__(**kwargs)
        self.retriever = retriever
        self.top_k = int(top_k)

    def _run(self, topic: str, num_questions: int = 3) -> str:
        docs: List[Document] = self.retriever.retrieve(topic, k=min(self.top_k, num_questions))
        if not docs:
            return json.dumps(
                {"topic": topic, "questions": [], "note": "No quiz data available."}
            )

        questions = []
        for i, doc in enumerate(docs[:num_questions]):
            meta = getattr(doc, "metadata", {}) or {}
            title = meta.get("title", "Unknown Title")
            year = meta.get("year", "Unknown Year")
            correct = str(year)

            distractors: List[str] = []
            try:
                y = int(year)
                distractors = [str(y - 1), str(y + 1), str(y + 2)]
            except Exception:
                distractors = ["1999", "2005", "2010"]

            # Deduplicate while preserving order, limit to 3 options
            options = []
            for opt in [correct] + distractors:
                if opt not in options:
                    options.append(opt)
                if len(options) == 3:
                    break

            questions.append(
                {
                    "id": i + 1,
                    "question": f"What year was '{title}' released?",
                    "options": options,
                    "answer": correct,
                }
            )

        return json.dumps({"topic": topic, "questions": questions})

    async def _arun(self, topic: str, num_questions: int = 3) -> str:
        return self._run(topic, num_questions=num_questions)


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
        "Check a user's quiz answer. Input question, user_answer, correct_answer. "
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
        "Compare two movies on basic metadata (year, genres, director) using the retriever."
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
                return {"title": "Unknown", "year": "Unknown", "genres": [], "director": "Unknown"}
            meta = getattr(doc, "metadata", {}) or {}
            return {
                "title": meta.get("title", "Unknown"),
                "year": meta.get("year", "Unknown"),
                "genres": meta.get("genres", meta.get("genre", [])),
                "director": meta.get("director", "Unknown"),
            }

        a_meta = meta_summary(a_doc)
        b_meta = meta_summary(b_doc)

        aspects = aspects or ["title", "year", "genres", "director"]
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

