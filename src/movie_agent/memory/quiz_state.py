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
    mode: Optional[str] = None  # actor | director | year | random
    current_question: Optional[str] = None
    current_question_id: Optional[int] = None
    current_question_index: int = 0  # Index in questions array (0-based)
    attempts: int = 0
    score: int = 0  # Number of correct answers
    quiz_data: Optional[Dict[str, Any]] = field(default_factory=dict)  # Full quiz JSON with answers
    history: List[Dict[str, Any]] = field(default_factory=list)  # History of answered questions
    
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
        # Extract mode from quiz data if available
        if quiz_data and "topic" in quiz_data:
            topic = str(quiz_data["topic"]).lower()
            if "actor" in topic:
                self.mode = "actor"
            elif "director" in topic:
                self.mode = "director"
            elif "year" in topic:
                self.mode = "year"
            else:
                self.mode = "random"
    
    def deactivate(self) -> None:
        """Deactivate quiz state."""
        self.active = False
        self.mode = None
        self.current_question = None
        self.current_question_id = None
        self.current_question_index = 0
        self.attempts = 0
        self.score = 0
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
        """Get total number of questions in quiz."""
        if not self.quiz_data:
            return 0
        return len(self.quiz_data.get("questions", []))
    
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
        if not self.active or not self.quiz_data:
            return False, None
        
        questions = self.quiz_data.get("questions", [])
        if self.current_question_index >= len(questions):
            return False, None
        
        current_q = questions[self.current_question_index]
        correct_answer = str(current_q.get("answer", ""))
        options = current_q.get("options", [])
        
        # Normalize user answer
        user_answer = str(user_answer).strip().lower()
        
        # Check if user answered with option number (1, 2, 3)
        try:
            option_num = int(user_answer)
            if 1 <= option_num <= len(options):
                selected_option = str(options[option_num - 1]).strip().lower()
                is_correct = selected_option == correct_answer.lower()
            else:
                is_correct = False
        except ValueError:
            # Check if user answered with option text or year
            is_correct = user_answer == correct_answer.lower()
        
        correct_answer_text = correct_answer
        
        return is_correct, correct_answer_text
    
    def record_answer(self, user_answer: str, is_correct: bool) -> None:
        """
        Record answer in history.
        
        :param user_answer: User's answer
        :param is_correct: Whether answer was correct
        """
        if not self.active or not self.quiz_data:
            return
        
        questions = self.quiz_data.get("questions", [])
        if self.current_question_index >= len(questions):
            return
        
        current_q = questions[self.current_question_index]
        self.history.append({
            "question_id": current_q.get("id"),
            "question": current_q.get("question"),
            "user_answer": user_answer,
            "correct_answer": current_q.get("answer"),
            "is_correct": is_correct,
            "attempts": self.attempts
        })
    
    def is_active(self) -> bool:
        """Check if quiz is active."""
        return self.active
    
    def is_complete(self) -> bool:
        """Check if quiz is complete (all questions answered)."""
        if not self.active:
            return False
        return self.current_question_index >= self.get_total_questions()

