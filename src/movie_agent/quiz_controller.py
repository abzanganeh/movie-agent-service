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
from .memory.quiz_state import QuizState

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
        logger.debug(f"QuizController initialized: score={self.score}, total={self.total_questions}, active={quiz_state.is_active()}")
    
    def handle_answer(self, user_answer: str) -> Tuple[str, bool, Optional[str]]:
        """
        Handle quiz answer submission.
        
        This is the single entry point for processing quiz answers.
        The controller validates the answer and advances state - no LLM involvement.
        
        Uses the same validation logic as the old working version to ensure correctness.
        
        :param user_answer: User's answer to current question
        :return: Tuple of (feedback_message, is_correct, correct_answer)
        """
        if not self._quiz_state.is_active():
            logger.warning("handle_answer called but quiz is not active")
            return "No quiz is currently active. Would you like to start one?", False, None
        
        if self._quiz_state.is_complete():
            logger.warning("handle_answer called but quiz is complete")
            return "The quiz is already complete!", False, None
        
        # CRITICAL: Check answer BEFORE advancing (same order as old working version)
        # This ensures we're checking against the current question, not the next one
        
        # Increment attempts (controller owns state management)
        self._quiz_state.increment_attempts()
        
        # Validate answer using quiz state (controller owns validation logic)
        # This uses the same logic as the old working version
        is_correct, correct_answer = self._quiz_state.check_answer(user_answer)
        
        # Update score if correct (controller owns score management)
        # CRITICAL: Update score BEFORE recording/logging so score is accurate
        if is_correct:
            self._quiz_state.increment_score()
        
        # Record the answer in history (controller owns history)
        # This records which question was answered (using current index)
        self._quiz_state.record_answer(user_answer, is_correct)
        
        # Generate feedback message (controller owns feedback generation)
        # Use encouraging messages, not "Quiz Complete!" - that only shows at the very end
        if is_correct:
            feedback = f"✅ Great job! The answer was {correct_answer}. Well done! 🎉"
        else:
            feedback = f"❌ Not quite. The correct answer was {correct_answer}. Don't worry, try again next time! 💪"
        
        # CRITICAL: DO NOT auto-advance - wait for user confirmation
        # User will need to say "yes", "next", "continue", or press enter to advance
        
        # Log with updated score (after increment if correct)
        logger.info(
            f"Answer processed: correct={is_correct}, "
            f"score={self.score}/{self.total_questions}, "
            f"question_index={self._quiz_state.current_question_index} (NOT advanced - waiting for user confirmation)"
        )
        
        return feedback, is_correct, correct_answer
    
    def advance_to_next_question(self) -> bool:
        """
        Advance to the next question after user confirms they want to continue.
        
        :return: True if there are more questions, False if quiz is complete
        """
        if not self._quiz_state.is_active():
            logger.warning("advance_to_next_question called but quiz is not active")
            return False
        
        # Advance to next question
        has_more = self._quiz_state.advance_to_next_question()
        
        logger.info(
            f"Question advanced: has_more={has_more}, "
            f"question_index={self._quiz_state.current_question_index}, "
            f"score={self.score}/{self.total_questions}"
        )
        
        return has_more
    
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
        
        Uses cached final score if quiz was deactivated.
        
        :return: Quiz completion data dict
        """
        # Use final score if available (quiz was deactivated), otherwise use current score
        final_score = getattr(self._quiz_state, '_final_score', 0)
        if final_score == 0:
            final_score = self._quiz_state.score
        
        return {
            "quiz_active": False,
            "quiz_complete": True,
            "score": final_score,
            "total": self._quiz_state.get_total_questions(),
            "topic": self._quiz_state.quiz_data.get("topic", "movies") if self._quiz_state.quiz_data else "movies"
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
    
    def is_last_question(self) -> bool:
        """
        Check if current question is the last one.
        
        :return: True if current question is the last, False otherwise
        """
        if not self._quiz_state.is_active():
            return False
        current_index = self._quiz_state.current_question_index
        total = self._quiz_state.get_total_questions()
        return (current_index + 1) >= total
    
    def complete_quiz(self) -> Dict[str, Any]:
        """
        Complete the quiz (advance to end, which deactivates).
        
        :return: Completion data dictionary
        """
        if self._quiz_state.is_active():
            self._quiz_state.advance_to_next_question()  # This will deactivate
        return self.get_completion_data()
    
    def deactivate_quiz(self) -> None:
        """
        Deactivate the quiz (stop quiz, return to normal flow).
        
        OOP: Controller owns quiz lifecycle management.
        """
        if self._quiz_state.is_active():
            self._quiz_state.deactivate()
            logger.info("Quiz deactivated by controller")
    
    @property
    def score(self) -> int:
        """Get current score."""
        return self._quiz_state.score
    
    @property
    def total_questions(self) -> int:
        """Get total number of questions."""
        return self._quiz_state.get_total_questions()
    
    def handle_navigation(self, user_input: str) -> Tuple[Optional[Dict[str, Any]], str, bool]:
        """
        Handle quiz navigation (next/continue/stop).
        
        OOP: Encapsulation - all navigation logic is in the controller.
        Service layer just delegates to this method.
        
        :param user_input: User's navigation input (e.g., "next", "continue", "stop")
        :return: Tuple of (quiz_data, answer_message, should_stop_quiz)
        """
        user_lower = user_input.lower().strip()
        
        # Check if user wants to stop quiz
        # OOP: Encapsulation - stop patterns are defined here, not in service layer
        stop_patterns = [
            'no', 'n', 'nope', 'stop', 'quit', 'end', 'exit', 'done', 'finish', 
            'enough', 'finish game', 'quit game', 'end game', 'stop game',
            'finish quiz', 'quit quiz', 'end quiz', 'stop quiz'
        ]
        # Check exact match or if any stop word/phrase appears in the input
        if user_lower in stop_patterns or any(phrase in user_lower for phrase in stop_patterns):
            self.deactivate_quiz()
            logger.info("User requested to stop quiz - deactivated")
            return None, "", True  # should_stop_quiz = True means fall through to normal flow
        
        # User wants to continue - advance to next question
        is_last = self.is_last_question()
        has_more = self.advance_to_next_question()
        
        if has_more:
            # More questions available - serve the next one
            current_q_data = self.get_current_question_data()
            if current_q_data:
                next_question = current_q_data["question"]
                options = ", ".join(current_q_data["options"])
                answer = f"📝 Question {current_q_data['progress']['current']} of {current_q_data['progress']['total']}:\n{next_question}\nOptions: {options}\n\n(Answer with the number or year)"
                logger.info(f"📤 Serving question {current_q_data['progress']['current']} of {current_q_data['progress']['total']}")
                return current_q_data, answer, False
            else:
                logger.error(f"❌ advance_to_next_question returned True but get_current_question_data returned None. Quiz active: {self._quiz_state.is_active()}, index: {self._quiz_state.current_question_index}, total: {self._quiz_state.get_total_questions()}")
                return None, "Error: Could not get next question.", False
        else:
            # Quiz complete (we were on the last question and advancing completed it)
            completion_data = self.get_completion_data()
            final_score = completion_data.get("score", 0)
            final_total = completion_data.get("total", 0)
            
            # OOP: Encapsulation - message formatting is controller's responsibility
            if final_score == final_total:
                score_message = f"🎉 Perfect score! You got all {final_total} questions correct! Amazing work! 🌟"
            elif final_score >= final_total * 0.7:
                score_message = f"🎉 Great job! You got {final_score} out of {final_total} correct! Well done! 👏"
            else:
                score_message = f"📊 You got {final_score} out of {final_total} correct. Keep practicing! 💪"
            
            answer = f"{score_message}\n\n🎯 Quiz Complete!\n\nWould you like to play again? (Type 'yes', 'play', or 'let's play')"
            logger.info(f"📤 Quiz completed: score={final_score}/{final_total}")
            return completion_data, answer, False

