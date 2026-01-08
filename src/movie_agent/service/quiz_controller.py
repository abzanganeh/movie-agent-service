"""
Quiz Controller - Manages quiz state and progression.

This controller handles all quiz-related operations following OOP principles:
- Single Responsibility: Only manages quiz flow
- Encapsulation: State is managed internally
- Separation of Concerns: LLM generates quiz, controller manages progression

The LLM should NEVER control quiz progression - only the controller does.
"""
import logging
from typing import Dict, Any, Optional, Tuple
from ..memory.quiz_state import QuizState

logger = logging.getLogger(__name__)


class QuizController:
    """
    Controller for managing quiz state and progression.
    
    This class is responsible for:
    - Validating quiz answers
    - Advancing quiz state
    - Serving next questions
    - Managing quiz lifecycle
    
    The LLM should NOT make decisions about quiz progression - only this controller does.
    """
    
    def __init__(self, quiz_state: QuizState):
        """
        Initialize quiz controller with quiz state.
        
        :param quiz_state: QuizState instance to manage
        """
        self._quiz_state = quiz_state
    
    def handle_answer(self, user_answer: str) -> Tuple[str, bool, Optional[str]]:
        """
        Handle quiz answer submission.
        
        This is the single entry point for processing quiz answers.
        The controller validates the answer and advances state - no LLM involvement.
        
        :param user_answer: User's answer to current question
        :return: Tuple of (feedback_message, is_correct, correct_answer)
        """
        if not self._quiz_state.is_active():
            logger.warning("handle_answer called but quiz is not active")
            return "No quiz is currently active. Would you like to start one?", False, None
        
        if self._quiz_state.is_complete():
            logger.warning("handle_answer called but quiz is complete")
            return "The quiz is already complete!", False, None
        
        # Validate answer using quiz state (controller owns validation logic)
        is_correct, correct_answer = self._quiz_state.check_answer(user_answer)
        
        # Record the answer in history
        self._quiz_state.record_answer(user_answer, is_correct)
        
        # Update score if correct
        if is_correct:
            self._quiz_state.increment_score()
        
        # Generate feedback message
        if is_correct:
            feedback = f"Correct! The answer was {correct_answer}."
        else:
            feedback = f"Incorrect. The correct answer was {correct_answer}."
        
        # Advance to next question (controller owns progression)
        has_more = self._quiz_state.advance_to_next_question()
        
        logger.debug(
            f"Answer processed: correct={is_correct}, "
            f"score={self._quiz_state.score}/{self._quiz_state.get_total_questions()}, "
            f"has_more={has_more}"
        )
        
        return feedback, is_correct, correct_answer
    
    def get_current_question_data(self) -> Optional[Dict[str, Any]]:
        """
        Get current question data for display.
        
        :return: Quiz data dict with current question, or None if quiz is not active
        """
        if not self._quiz_state.is_active():
            return None
        
        current_q = self._quiz_state.get_current_question()
        if not current_q:
            return None
        
        return {
            "quiz_active": True,
            "question_id": current_q.get("id"),
            "question": current_q.get("question"),
            "options": current_q.get("options", []),
            "progress": {
                "current": self._quiz_state.current_question_index + 1,
                "total": self._quiz_state.get_total_questions()
            },
            "topic": self._quiz_state.quiz_data.get("topic", "movies"),
            "mode": self._quiz_state.mode
        }
    
    def get_completion_data(self) -> Dict[str, Any]:
        """
        Get quiz completion data.
        
        :return: Quiz completion data dict
        """
        return {
            "quiz_active": False,
            "quiz_complete": True,
            "score": self._quiz_state.score,
            "total": self._quiz_state.get_total_questions(),
            "topic": self._quiz_state.quiz_data.get("topic", "movies")
        }
    
    def activate_quiz(self, quiz_data: Dict[str, Any]) -> None:
        """
        Activate quiz with quiz data.
        
        :param quiz_data: Quiz data from generate_movie_quiz tool
        """
        # Filter out previously asked questions
        asked_ids = self._quiz_state.get_asked_question_ids()
        if asked_ids and quiz_data.get("questions"):
            questions = quiz_data.get("questions", [])
            quiz_data["questions"] = [q for q in questions if q.get("id") not in asked_ids]
        
        self._quiz_state.activate(quiz_data)
        logger.debug(f"Quiz activated with {self._quiz_state.get_total_questions()} questions")
    
    def is_active(self) -> bool:
        """Check if quiz is active."""
        return self._quiz_state.is_active()
    
    def is_complete(self) -> bool:
        """Check if quiz is complete."""
        return self._quiz_state.is_complete()
    
    @property
    def score(self) -> int:
        """Get current score."""
        return self._quiz_state.score
    
    @property
    def total_questions(self) -> int:
        """Get total number of questions."""
        return self._quiz_state.get_total_questions()



