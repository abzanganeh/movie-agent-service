"""
Quiz state management.

Tracks quiz session state explicitly.
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List


@dataclass
class QuizState:
    """
    Quiz session state object.
    Tracks quiz progress, current question, score, and history.
    """
    active: bool = False
    mode: Optional[str] = None  # actor | director | year | random (deprecated, use quiz_type)
    quiz_type: Optional[str] = None  # 'cast' | 'director' | 'year' - current quiz type
    current_question: Optional[str] = None
    current_question_id: Optional[int] = None
    current_question_index: int = 0  # Index in questions array (0-based)
    attempts: int = 0
    score: int = 0  # Number of correct answers
    quiz_data: Optional[Dict[str, Any]] = field(default_factory=dict)  # Full quiz JSON with answers
    history: List[Dict[str, Any]] = field(default_factory=list)  # History of answered questions
    _total_questions: int = 0  # Cache total questions count (preserved after deactivation for final score display)
    _final_score: int = 0  # Cache final score (preserved after deactivation for final score display)
    
    def activate(self, quiz_data: Dict[str, Any], question_id: Optional[int] = None) -> None:
        """
        Activate quiz state with quiz data.
        Resets to first question.
        
        :param quiz_data: Quiz JSON data from generate_movie_quiz
        :param question_id: Optional current question ID (defaults to 0)
        """
        self.active = True
        self.quiz_data = quiz_data
        self.current_question_index = 0
        self.current_question_id = question_id if question_id is not None else 0
        self.attempts = 0
        self.score = 0
        self.history = []
        # Cache total questions count (preserved after deactivation for final score display)
        self._total_questions = len(quiz_data.get("questions", [])) if quiz_data else 0
        # Extract mode from quiz data (OOP: use explicit quiz_type field if available, fallback to topic parsing)
        if quiz_data:
            # First, try explicit quiz_type field (from new Strategy Pattern implementation)
            quiz_type = quiz_data.get("quiz_type", "").lower()
            if quiz_type in ["year", "director", "cast"]:
                self.mode = quiz_type
            # Fallback: parse from topic (for backward compatibility)
            elif "topic" in quiz_data:
                topic = str(quiz_data["topic"]).lower()
                if "actor" in topic or "cast" in topic:
                    self.mode = "cast"
                elif "director" in topic:
                    self.mode = "director"
                elif "year" in topic:
                    self.mode = "year"
                else:
                    self.mode = "year"  # Default to year
            else:
                self.mode = "year"  # Default to year
        else:
            self.mode = "year"  # Default to year
    
    def deactivate(self) -> None:
        """
        Deactivate quiz state.
        
        Note: Score is preserved in _final_score if quiz completed normally.
        quiz_type is preserved for continuation.
        """
        self.active = False
        self.mode = None
        # Preserve quiz_type for continuation (don't reset it)
        # self.quiz_type = None  # Keep quiz_type so user can continue with same type
        self.current_question = None
        self.current_question_id = None
        self.current_question_index = 0
        self.attempts = 0
        self.score = 0  # Reset current score, but _final_score preserves the completion score
        self.quiz_data = {}
        self.history = []
    
    def increment_attempts(self) -> None:
        """Increment attempt counter."""
        self.attempts += 1
    
    def increment_score(self) -> None:
        """Increment score (correct answer)."""
        self.score += 1
    
    def get_current_question(self) -> Optional[Dict[str, Any]]:
        """
        Get current question data (without answer).
        
        :return: Question dict with id, question, options (no answer field)
        """
        if not self.active or not self.quiz_data:
            return None
        
        questions = self.quiz_data.get("questions", [])
        if self.current_question_index >= len(questions):
            return None
        
        q = questions[self.current_question_index].copy()
        # Remove answer before returning
        q.pop("answer", None)
        return q
    
    def get_total_questions(self) -> int:
        """
        Get total number of questions in quiz.
        
        Uses cached count if quiz_data is cleared (after deactivation),
        otherwise calculates from quiz_data.
        """
        if self.quiz_data and "questions" in self.quiz_data:
            return len(self.quiz_data.get("questions", []))
        # Return cached count if quiz_data was cleared (after completion)
        return self._total_questions
    
    def advance_to_next_question(self) -> bool:
        """
        Advance to next question.
        
        :return: True if there are more questions, False if quiz is complete
        """
        if not self.active:
            return False
        
        self.current_question_index += 1
        self.attempts = 0  # Reset attempts for new question
        
        total = self.get_total_questions()
        if self.current_question_index >= total:
            # CRITICAL: Preserve score before deactivating (for final score display)
            self._final_score = self.score
            self.deactivate()
            return False
        
        if self.quiz_data and "questions" in self.quiz_data:
            questions = self.quiz_data["questions"]
            if self.current_question_index < len(questions):
                self.current_question_id = questions[self.current_question_index].get("id")
        
        return True
    
    def check_answer(self, user_answer: str) -> tuple[bool, Optional[str]]:
        """
        Check user answer against current question.
        
        :param user_answer: User's answer (can be number, option text, or year)
        :return: Tuple of (is_correct, correct_answer)
        """
        import logging
        logger = logging.getLogger(__name__)
        
        if not self.active or not self.quiz_data:
            logger.warning(f"check_answer called but quiz not active or no quiz_data. active={self.active}, has_data={bool(self.quiz_data)}")
            return False, None
        
        questions = self.quiz_data.get("questions", [])
        if self.current_question_index >= len(questions):
            logger.warning(f"check_answer: question_index {self.current_question_index} >= {len(questions)} questions")
            return False, None
        
        current_q = questions[self.current_question_index]
        correct_answer = str(current_q.get("answer", ""))
        options = current_q.get("options", [])
        
        # Normalize user answer
        user_answer_normalized = str(user_answer).strip().lower()
        
        # Normalize correct answer for comparison
        correct_answer_normalized = str(correct_answer).strip().lower()
        
        logger.info(f"🔍 check_answer: user_input='{user_answer}' (normalized: '{user_answer_normalized}'), correct='{correct_answer}' (normalized: '{correct_answer_normalized}'), options={options}, question_index={self.current_question_index}")
        
        # Check if user answered with option number (1, 2, 3)
        # CRITICAL FIX: Only treat as option number if it's in valid range (1-3)
        # Years like "1988" are valid integers but should be treated as year answers, not option numbers
        try:
            option_num = int(user_answer_normalized)
            # Only treat as option number if it's in the valid range (1 to number of options)
            if 1 <= option_num <= len(options):
                selected_option = str(options[option_num - 1]).strip().lower()
                is_correct = selected_option == correct_answer_normalized
                logger.info(f"✅ Option number {option_num} selected: '{selected_option}' == '{correct_answer_normalized}'? {is_correct}")
            else:
                # Integer but out of range - treat as year answer (e.g., "1988" is not option 1988)
                is_correct = user_answer_normalized == correct_answer_normalized
                logger.info(f"📅 Year answer (out of range): '{user_answer_normalized}' == '{correct_answer_normalized}'? {is_correct}")
        except ValueError:
            # Not an integer - treat as text answer (both normalized)
            is_correct = user_answer_normalized == correct_answer_normalized
            logger.info(f"📝 Text answer: '{user_answer_normalized}' == '{correct_answer_normalized}'? {is_correct}")
        
        correct_answer_text = correct_answer
        
        logger.info(f"check_answer result: is_correct={is_correct}, correct_answer='{correct_answer_text}', question_index={self.current_question_index}")
        
        return is_correct, correct_answer_text
    
    def record_answer(self, user_answer: str, is_correct: bool) -> None:
        """
        Record answer in history.
        
        CRITICAL: This must be called BEFORE advance_to_next_question()
        to record the answer for the current question index.
        
        :param user_answer: User's answer
        :param is_correct: Whether answer was correct
        """
        if not self.active or not self.quiz_data:
            return
        
        questions = self.quiz_data.get("questions", [])
        if self.current_question_index >= len(questions):
            logger.warning(f"record_answer: question_index {self.current_question_index} >= {len(questions)} questions")
            return
        
        current_q = questions[self.current_question_index]
        self.history.append({
            "question_id": current_q.get("id"),
            "question": current_q.get("question"),
            "user_answer": user_answer,
            "correct_answer": current_q.get("answer"),
            "is_correct": is_correct,
            "attempts": self.attempts,
            "question_index": self.current_question_index  # Store index for debugging
        })
    
    def is_active(self) -> bool:
        """Check if quiz is active."""
        return self.active
    
    def is_complete(self) -> bool:
        """Check if quiz is complete (all questions answered)."""
        if not self.active:
            return False
        return self.current_question_index >= self.get_total_questions()
    
    def get_asked_question_ids(self) -> List[int]:
        """
        Get list of question IDs that have been asked.
        
        :return: List of question IDs from history
        """
        return [item.get("question_id") for item in self.history if item.get("question_id") is not None]
    
    def has_been_asked(self, question_id: int) -> bool:
        """
        Check if a question has already been asked.
        
        :param question_id: Question ID to check
        :return: True if question has been asked, False otherwise
        """
        return question_id in self.get_asked_question_ids()
    
    def get_asked_questions(self) -> List[Dict[str, Any]]:
        """
        Get list of all questions that have been asked.
        
        :return: List of question dictionaries from history
        """
        return self.history.copy()

