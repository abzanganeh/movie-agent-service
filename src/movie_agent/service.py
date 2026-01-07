from typing import Optional, List, Dict, Any
from time import time
import logging
import json
import re

from .config import MovieAgentConfig

logger = logging.getLogger(__name__)
from .exceptions import AgentNotInitializedError, VisionAnalystNotInitializedError
from .schemas import ChatResponse, PosterAnalysisResponse
from .models import Movie
from .tools import (
    RetrieverTool,
    VisionTool,
    GenerateMovieQuizTool,
    CheckQuizAnswerTool,
    CompareMoviesTool,
    SearchActorTool,
    SearchDirectorTool,
    SearchYearTool,
    MovieStatisticsTool,
)
from .agent.tool_calling_agent import ToolCallingAgent
from .agent.prompts import MOVIE_PROMPT
from .tools.impl import MovieSearchTool, PosterAnalysisTool
from .memory import SessionMemoryManager
from .memory.session_state import SessionStateManager
from .memory.quiz_state import QuizState
from .intent import AgentIntent, detect_intent
from .quiz_controller import QuizController
from .context import SessionContextManager
from .orchestration.poster_orchestrator import PosterOrchestrator
from .orchestration.chat_orchestrator import ChatOrchestrator


class MovieAgentService:
    """
    Facade over the movie AI agent subsystem.
    The ONLY entry point for the UI layers.
    """

    def __init__(self, config: MovieAgentConfig):
        """
        Initialize the service with configuration.
        """
        self.config = config

        self._agent: Optional[object] = None
        self._vector_store: Optional[RetrieverTool] = None
        self._vision_analyst: Optional[VisionTool] = None
        self._movies: Optional[List[Movie]] = None
        self._session_memory: Optional[SessionMemoryManager] = None
        self._session_state: SessionStateManager = SessionStateManager()
        self._session_context: SessionContextManager = SessionContextManager()

        if self.config.enable_memory:
            self._session_memory = SessionMemoryManager(
                max_turns_per_session=self.config.memory_max_turns
            )

        if self.config.warmup_on_start:
            self.warmup()
    
    def _get_conversation_history(self, session_id: str) -> str:
        """
        Retrieve and format conversation history from session memory.
        
        :param session_id: Session identifier
        :return: Formatted conversation history string, or empty string if no history
        """
        if not self._session_memory:
            return ""
        
        conversation_mem = self._session_memory.get_conversation_memory(session_id)
        if not conversation_mem:
            return ""
        
        chat_history = conversation_mem.format_as_chat_history()
        if not chat_history:
            return ""
        
        return f"Previous conversation:\n{chat_history}\n"

    def warmup(self) -> None:
        """
        Preload heavy resources (models, vector store, etc.).
        """
        if self._agent:
            return

        if not self._vector_store:
            raise RuntimeError("Retriever tool must be injected before warmup.")

        tools = []
        search_tool = MovieSearchTool(retriever=self._vector_store)
        tools.append(search_tool)
        self._search_tool = search_tool

        tools.append(GenerateMovieQuizTool(retriever=self._vector_store))
        tools.append(CheckQuizAnswerTool())
        tools.append(CompareMoviesTool(retriever=self._vector_store))
        tools.append(SearchActorTool(retriever=self._vector_store))
        tools.append(SearchDirectorTool(retriever=self._vector_store))
        tools.append(SearchYearTool(retriever=self._vector_store))
        
        if self._movies:
            tools.append(MovieStatisticsTool(movies=self._movies))

        if self.config.enable_vision:
            if not self._vision_analyst:
                raise RuntimeError("Vision tool must be injected when enable_vision=True.")
            vision_tool = PosterAnalysisTool(vision_tool=self._vision_analyst)
            tools.append(vision_tool)

        prompt = MOVIE_PROMPT.partial(tool_names=[t.name for t in tools])
        
        self._agent = ToolCallingAgent(
            llm=self.config.llm,
            tools=tools,
            prompt=prompt,
            verbose=self.config.verbose,
        )


    def chat(self, user_message: str, session_id: str = "default") -> ChatResponse:
        """
        Handle user chat query with optional session ID.
        
        :param user_message: User's message
        :param session_id: Session identifier (defaults to "default" for single-user scenarios)
        :return: ChatResponse with answer and metadata
        """
        if not self._agent:
            raise AgentNotInitializedError("Agent is not initialized.")

        if self._session_memory:
            self._session_memory.record(session_id, {
                "type": "user_query",
                "content": user_message,
                "role": "user",
            })

        session_state = self._session_state.get_state(session_id)
        quiz_state = session_state.get_quiz_state()
        
        # CRITICAL: Process any pending quiz activation FIRST (from previous request)
        # This ensures quiz state is active before intent detection
        # Check if there's a pending quiz activation in session state
        # (This handles the case where generate_movie_quiz was called in previous request)
        
        # Check quiz state BEFORE intent detection to ensure accurate intent routing
        quiz_active = quiz_state.is_active()
        
        # Debug: Log quiz state for troubleshooting
        if quiz_active:
            logger.info(f"✅ Quiz is ACTIVE for session {session_id[:8]}, question index: {quiz_state.current_question_index}, score: {quiz_state.score}/{quiz_state.get_total_questions()}")
        else:
            logger.warning(f"❌ Quiz is NOT active for session {session_id[:8]}. Quiz data exists: {bool(quiz_state.quiz_data)}, active flag: {quiz_state.active}")
        
        intent = detect_intent(user_message, quiz_active=quiz_active)
        
        # CRITICAL FIX: If quiz is active, ANY input that's not explicit navigation/start is a quiz answer
        # This overrides intent detection to ensure quiz answers are always handled correctly
        original_intent = intent
        if quiz_active and intent != AgentIntent.QUIZ_NEXT and intent != AgentIntent.QUIZ_START:
            intent = AgentIntent.QUIZ_ANSWER
            logger.info(f"🔄 Overriding intent to QUIZ_ANSWER (quiz is active, original intent was {original_intent.value})")
        
        # Create quiz controller for managing quiz state (OOP: Single Responsibility)
        quiz_controller = QuizController(quiz_state)
        
        # Handle QUIZ_ANSWER intent - controller manages quiz progression (NO LLM INVOLVEMENT)
        # This is the critical fix: Controller owns quiz state, not the LLM
        if intent == AgentIntent.QUIZ_ANSWER:
            if not quiz_state.is_active():
                # Quiz state not active - this shouldn't happen if quiz was properly activated
                logger.warning(f"⚠️ QUIZ_ANSWER intent detected but quiz is NOT active! User said: {user_message[:50]}")
                # Try to recover by checking if quiz data exists but state is inactive
                if quiz_state.quiz_data and quiz_state.quiz_data.get("questions"):
                    logger.info("🔄 Attempting to reactivate quiz from existing quiz_data...")
                    quiz_controller = QuizController(quiz_state)
                    quiz_controller.activate_quiz(quiz_state.quiz_data)
                    # Re-check after reactivation
                    if quiz_state.is_active():
                        logger.info("✅ Quiz reactivated successfully")
                    else:
                        logger.error("❌ Failed to reactivate quiz")
                        # Return error response instead of continuing
                        error_response = ChatResponse(
                            answer="Quiz state error. Please start a new quiz with 'let's play'.",
                            movies=[],
                            tools_used=[],
                            llm_latency_ms=0,
                            tool_latency_ms=0,
                            latency_ms=0,
                            reasoning_type="error",
                            confidence=0.0
                        )
                        return error_response
                else:
                    # No quiz data to recover from
                    error_response = ChatResponse(
                        answer="No quiz is currently active. Please start a new quiz with 'let's play'.",
                        movies=[],
                        tools_used=[],
                        llm_latency_ms=0,
                        tool_latency_ms=0,
                        latency_ms=0,
                        reasoning_type="error",
                        confidence=0.0
                    )
                    return error_response
            
            if quiz_state.is_active():
                # Controller validates answer and advances state directly
                feedback, is_correct, correct_answer = quiz_controller.handle_answer(user_message)
            
                # Determine what to show next
                if quiz_controller.is_complete():
                    # Quiz complete - show final score and ask if they want to play again
                    quiz_data = quiz_controller.get_completion_data()
                    answer = f"{feedback}\n\n🎉 Quiz Complete!\n\nYour final score: {quiz_controller.score}/{quiz_controller.total_questions}\n\nWould you like to play again? (Type 'yes' or 'let's play')"
                elif quiz_controller.is_active():
                    # Get next question from controller
                    current_q_data = quiz_controller.get_current_question_data()
                    if current_q_data:
                        quiz_data = current_q_data
                        next_question = current_q_data["question"]
                        options = ", ".join(current_q_data["options"])
                        # Add "continue" prompt
                        answer = f"{feedback}\n\n📝 Question {current_q_data['progress']['current']} of {current_q_data['progress']['total']}:\n{next_question}\nOptions: {options}"
                    else:
                        # Should not happen, but handle gracefully
                        quiz_data = None
                        answer = feedback
                else:
                    # Quiz was deactivated (should not happen after handle_answer)
                    quiz_data = None
                    answer = feedback
                
                # Build response (no LLM, no tools - controller handled everything)
                response = ChatResponse(
                    answer=answer,
                    movies=[],
                    tools_used=[],
                    llm_latency_ms=0,
                    tool_latency_ms=0,
                    latency_ms=0,
                    reasoning_type="quiz_answer_controller",
                    confidence=1.0,
                    quiz_data=quiz_data
                )
                
                # Record in memory
                if self._session_memory:
                    self._session_memory.record(session_id, {
                        "type": "assistant_response",
                        "content": answer,
                        "role": "assistant",
                        "intent": intent.value,
                    })
                
                logger.info(f"✅ Quiz answer handled by controller: correct={is_correct}, score={quiz_controller.score}/{quiz_controller.total_questions}")
                return response
        
        # Handle QUIZ_NEXT intent - advance to next question without calling tools
        if intent == AgentIntent.QUIZ_NEXT and quiz_state.is_active():
            # Advance to next question if available
            if not quiz_state.is_complete():
                quiz_state.advance_to_next_question()
            
            # Serve next question directly without calling agent
            current_q = quiz_state.get_current_question()
            if current_q:
                quiz_data = {
                    "quiz_active": True,
                    "question_id": current_q.get("id"),
                    "question": current_q.get("question"),
                    "options": current_q.get("options", []),
                    "progress": {
                        "current": quiz_state.current_question_index + 1,
                        "total": quiz_state.get_total_questions()
                    },
                    "topic": quiz_state.quiz_data.get("topic", "movies"),
                    "mode": quiz_state.mode
                }
                answer = f"Question {quiz_data['progress']['current']} of {quiz_data['progress']['total']}"
            else:
                # Quiz complete
                quiz_data = {
                    "quiz_active": False,
                    "quiz_complete": True,
                    "score": quiz_state.score,
                    "total": quiz_state.get_total_questions(),
                    "topic": quiz_state.quiz_data.get("topic", "movies")
                }
                answer = f"Quiz Complete!\n\nYour score: {quiz_state.score}/{quiz_state.get_total_questions()}"
            
            response = ChatResponse(
                answer=answer,
                movies=[],
                tools_used=[],
                llm_latency_ms=0,
                tool_latency_ms=0,
                latency_ms=0,
                reasoning_type="quiz_navigation",
                confidence=1.0,
                quiz_data=quiz_data
            )
            
            if self._session_memory:
                self._session_memory.record(session_id, {
                    "type": "assistant_response",
                    "content": answer,
                    "role": "assistant",
                    "intent": intent.value,
                })
            
            return response
        
        if intent == AgentIntent.CHIT_CHAT:
            greeting_responses = {
                "hi": "Hi! I can help you with movies, quizzes, comparisons, and statistics.",
                "hello": "Hello! I'm here to help with all things movies.",
                "hey": "Hey! What movie-related question can I help you with?",
                "thanks": "You're welcome! Feel free to ask me anything about movies.",
                "thank you": "You're welcome! Happy to help with movies.",
            }
            user_lower = user_message.lower().strip()
            answer = greeting_responses.get(user_lower, "Hi! I can help you with movies, quizzes, comparisons, and statistics. What would you like to know?")
            
            response = ChatResponse(
                answer=answer,
                movies=[],
                tools_used=[],
                llm_latency_ms=0,
                tool_latency_ms=0,
                latency_ms=0,
                reasoning_type="chit_chat",
                confidence=1.0
            )
            
            # Record in memory
            if self._session_memory:
                self._session_memory.record(session_id, {
                    "type": "assistant_response",
                    "content": answer,
                    "role": "assistant",
                    "intent": intent.value,
                })
            
            return response
        
        intent_context = ""
        if intent == AgentIntent.CORRECTION:
            intent_context = "\n[IMPORTANT: User is providing feedback/correction. Acknowledge the correction conversationally. Do NOT call any tools, especially NOT check_quiz_answer. Just acknowledge and ask how to help further.]"
        elif intent == AgentIntent.QUIZ_ANSWER and not quiz_state.is_active():
            # This should not happen since we handle QUIZ_ANSWER above, but keep for safety
            intent_context = "\n[IMPORTANT: User appears to be answering a quiz, but no quiz is active. Politely inform them that no quiz is currently running and ask if they'd like to start one.]"
        # REMOVED: QUIZ_ANSWER handling when quiz is active - this is now handled by controller above
        # The LLM should NEVER control quiz progression - only the controller does
        
        session_context = self._session_context.get_context(session_id)
        
        chat_orchestrator = ChatOrchestrator(
            agent=self._agent,
            session_context=session_context,
            session_state=session_state,
        )
        
        enriched_message = chat_orchestrator.enrich_message_with_context(user_message)
        if intent_context:
            enriched_message = intent_context + "\n" + enriched_message
        
        chat_history = self._get_conversation_history(session_id)
        
        # Always log poster context if available (for debugging)
        if session_context.has_poster():
            poster = session_context.poster
            logger.info(f"Poster context available - Title: {poster.title}, Mood: {poster.mood}, Caption: {poster.caption[:50]}...")
            logger.debug(f"Enriched message (first 500 chars): {enriched_message[:500]}...")
        elif self.config.verbose:
            logger.debug(f"Detected intent: {intent.value} for query: {user_message[:50]}...")

        start_time = time()
        
        try:
            result = self._agent.run(enriched_message, chat_history=chat_history)
        except Exception as e:
            logger.error(f"Agent execution failed: {e}", exc_info=True)
            return self._handle_tool_failure(
                user_message,
                str(e),
                int((time() - start_time) * 1000),
                session_id
            )
        
        total_latency_ms = int((time() - start_time) * 1000)
        
        movies = result.get("movies", [])
        confidence = result.get("confidence")
        if confidence is None:
            confidence = 1.0
        else:
            confidence = float(confidence)
        
        if (not movies and result.get("tools_used")) or (confidence < 0.5 and not movies):
            result = self._handle_partial_results(result, user_message, session_id)
        
        if self.config.verbose or ("poster" in user_message.lower() or "image" in user_message.lower()):
            logger.debug(f"Agent parsed result - Title: {result.get('title')}, Mood: {result.get('mood')}, Confidence: {result.get('confidence')}, Caption: {result.get('caption')}")

        llm_latency = result.get("llm_latency_ms")
        tool_latency = result.get("tool_latency_ms")
        
        validated_movies = result.get("movies", [])
        validation_confidence = result.get("confidence")
        if validation_confidence is None:
            validation_confidence = 1.0
        else:
            validation_confidence = float(validation_confidence)
        original_answer = result.get("answer", "")
        original_movies = result.get("movies", [])
        
        # Update session state FIRST (this may modify result["answer"] for check_quiz_answer)
        self._update_session_state(session_state, result.get("tools_used", []), result)
        
        # Now get the updated answer (may contain feedback from check_quiz_answer)
        updated_answer = result.get("answer", original_answer)
        
        # REMOVED: check_quiz_answer handling here
        # Quiz answers are now handled by QuizController before this point
        # The controller returns the response directly, so we never reach here for quiz answers
        
        if result.get("tools_used"):
            validated_movies, validation_confidence = self._validate_movie_results(
                validated_movies,
                user_message,
                result.get("tools_used", [])
            )
            
            if len(validated_movies) != len(original_movies):
                validated_answer = self._update_answer_with_validated_movies(
                    original_answer,
                    validated_movies,
                    original_movies
                )
            else:
                validated_answer = original_answer
        else:
            validated_answer = original_answer
        
        resolution_metadata = None
        if hasattr(self, '_search_tool') and self._search_tool:
            metadata = self._search_tool.get_last_resolution_metadata()
            if metadata:
                resolution_metadata = metadata.to_dict()
        
        # Handle quiz state BEFORE updating session state (to get current question before advancement)
        quiz_state = session_state.get_quiz_state()
        quiz_data = None
        was_check_quiz_answer = "check_quiz_answer" in result.get("tools_used", [])
        
        # If answer was checked, capture current question BEFORE state update advances it
        current_question_before_advance = None
        if was_check_quiz_answer and quiz_state.is_active():
            current_question_before_advance = quiz_state.get_current_question()
        
        # _update_session_state was already called above to ensure feedback is available
        
        # Handle quiz state - serve one question at a time
        if quiz_state.is_active():
            # If quiz was just generated, serve first question
            if "generate_movie_quiz" in result.get("tools_used", []):
                current_q = quiz_state.get_current_question()
                if current_q:
                    quiz_data = {
                        "quiz_active": True,
                        "question_id": current_q.get("id"),
                        "question": current_q.get("question"),
                        "options": current_q.get("options", []),
                        "progress": {
                            "current": quiz_state.current_question_index + 1,
                            "total": quiz_state.get_total_questions()
                        },
                        "topic": quiz_state.quiz_data.get("topic", "movies"),
                        "mode": quiz_state.mode
                    }
                    # Update answer to be quiz-friendly
                    validated_answer = f"Quiz: {quiz_state.quiz_data.get('topic', 'movies')}\n\nQuestion {quiz_data['progress']['current']} of {quiz_data['progress']['total']}"
            # If answer was checked, show feedback and auto-advance to next question
            elif was_check_quiz_answer:
                # Get feedback from result (set by _update_session_state)
                feedback_answer = result.get("answer", "")
                if feedback_answer:
                    validated_answer = feedback_answer
                    logger.debug(f"Set validated_answer from check_quiz_answer feedback: {feedback_answer[:50]}...")
                else:
                    logger.warning("check_quiz_answer was used but no feedback found in result['answer']")
                
                # After showing feedback, automatically serve next question
                # State was already advanced in _update_session_state, so get_current_question() returns next question
                if quiz_state.is_active() and not quiz_state.is_complete():
                    # Auto-advance: serve next question immediately (already advanced in _update_session_state)
                    current_q = quiz_state.get_current_question()
                    if current_q:
                        # Combine feedback with next question
                        next_question_text = f"{current_q.get('question')}\nOptions: {', '.join(current_q.get('options', []))}"
                        validated_answer = f"{validated_answer}\n\n{next_question_text}"
                        
                        quiz_data = {
                            "quiz_active": True,
                            "question_id": current_q.get("id"),
                            "question": current_q.get("question"),
                            "options": current_q.get("options", []),
                            "progress": {
                                "current": quiz_state.current_question_index + 1,
                                "total": quiz_state.get_total_questions()
                            },
                            "topic": quiz_state.quiz_data.get("topic", "movies"),
                            "mode": quiz_state.mode
                        }
                        logger.debug(f"Auto-advancing to next question: {current_q.get('question')[:50]}...")
                    else:
                        quiz_data = None
                        logger.warning("Quiz is active but no current question found")
                elif quiz_state.is_complete():
                    # Quiz complete - return final score
                    quiz_data = {
                        "quiz_active": False,
                        "quiz_complete": True,
                        "score": quiz_state.score,
                        "total": quiz_state.get_total_questions(),
                        "topic": quiz_state.quiz_data.get("topic", "movies")
                    }
                    validated_answer = f"{validated_answer}\n\nQuiz Complete!\n\nYour score: {quiz_state.score}/{quiz_state.get_total_questions()}"
                    logger.debug(f"Quiz completed with score: {quiz_state.score}/{quiz_state.get_total_questions()}")
            # If quiz is active but no tool was used, serve current question
            elif quiz_state.is_active():
                current_q = quiz_state.get_current_question()
                if current_q:
                    quiz_data = {
                        "quiz_active": True,
                        "question_id": current_q.get("id"),
                        "question": current_q.get("question"),
                        "options": current_q.get("options", []),
                        "progress": {
                            "current": quiz_state.current_question_index + 1,
                            "total": quiz_state.get_total_questions()
                        },
                        "topic": quiz_state.quiz_data.get("topic", "movies"),
                        "mode": quiz_state.mode
                    }

        response = ChatResponse(
            answer=validated_answer,
            movies=validated_movies,
            tools_used=result.get("tools_used", []),
            llm_latency_ms=llm_latency,
            tool_latency_ms=tool_latency,
            latency_ms=total_latency_ms,
            reasoning_type="tool_calling",
            resolution_metadata=resolution_metadata,
            confidence=validation_confidence,
            title=result.get("title"),
            mood=result.get("mood"),
            caption=result.get("caption"),
            quiz_data=quiz_data,
        )
        
        if self._session_memory:
            self._session_memory.record(session_id, {
                "type": "assistant_response",
                "content": response.answer,
                "role": "assistant",
                "movies": response.movies,
                "tools_used": response.tools_used,
                "intent": intent.value,
            })
        
        return response


    def analyze_poster(self, image_path: str, session_id: str = "default") -> PosterAnalysisResponse:
        """
        Analyze a movie poster using orchestrator pattern.
        
        :param image_path: Path to poster image file
        :param session_id: Session identifier for memory storage (defaults to "default")
        :return: PosterAnalysisResponse with title, mood, confidence, caption
        """
        if not self._vision_analyst:
            raise VisionAnalystNotInitializedError("Vision analyst is not initialized.")
        
        if not self._vector_store:
            raise RuntimeError("Retriever must be initialized for poster orchestration.")
        
        from .tools.movie_retriever import MovieRetriever
        
        if not isinstance(self._vector_store, MovieRetriever):
            raise RuntimeError("Poster orchestration requires MovieRetriever instance.")
        
        session_context = self._session_context.get_context(session_id)
        
        poster_orchestrator = PosterOrchestrator(
            vision_tool=self._vision_analyst,
            retriever=self._vector_store,
        )
        
        poster_context = poster_orchestrator.analyze_and_store(image_path, session_context)
        
        if self._session_memory:
            self._session_memory.record(session_id, {
                "type": "poster_analysis",
                "title": poster_context.title,
                "mood": poster_context.mood,
                "confidence": poster_context.confidence,
                "caption": poster_context.caption,
                "inferred_genres": poster_context.inferred_genres,
            })
        
        return PosterAnalysisResponse(
            caption=poster_context.caption,
            title=poster_context.title,
            mood=poster_context.mood,
            confidence=poster_context.confidence,
            inferred_genres=poster_context.inferred_genres,
        )

    def set_vector_store(self, vector_store: RetrieverTool) -> None:
        """Inject a retrieval tool."""
        self._vector_store = vector_store

    def set_vision_analyst(self, vision_tool: VisionTool) -> None:
        """Inject a vision analysis tool."""
        self._vision_analyst = vision_tool
    
    def set_movies(self, movies: List[Movie]) -> None:
        """Inject movie dataset for statistics tool."""
        self._movies = movies
    
    def _is_correction_or_feedback(self, user_message: str) -> bool:
        """
        Detect if user message is a correction or feedback.
        
        DEPRECATED: Use detect_intent() instead for intent classification.
        Kept for backward compatibility but delegates to detect_intent().
        
        :param user_message: User's message
        :return: True if message appears to be correction/feedback
        """
        intent = detect_intent(user_message, quiz_active=False)
        return intent == AgentIntent.CORRECTION
    
    def _extract_query_constraints(self, user_query: str) -> tuple[Optional[tuple[int, int]], Optional[str]]:
        """
        Extract year range and genre constraints from user query.
        
        :param user_query: User query text
        :return: Tuple of (year_range, target_genre)
        """
        query_lower = user_query.lower()
        
        year_range = None
        
        if "90s" in query_lower or "nineties" in query_lower or "1990s" in query_lower:
            year_range = (1990, 1999)
        elif "80s" in query_lower or "eighties" in query_lower or "1980s" in query_lower:
            year_range = (1980, 1989)
        elif "2000s" in query_lower or "00s" in query_lower or "noughties" in query_lower:
            year_range = (2000, 2009)
        elif "70s" in query_lower or "seventies" in query_lower or "1970s" in query_lower:
            year_range = (1970, 1979)
        elif "60s" in query_lower or "sixties" in query_lower or "1960s" in query_lower:
            year_range = (1960, 1969)
        else:
            year_pattern = r'\b(19|20)\d{2}\b'
            years = [int(m.group()) for m in re.finditer(year_pattern, query_lower)]
            if years:
                target_year = years[0]
                year_range = (target_year - 2, target_year + 2)
        
        genre_keywords = {
            "action": "action",
            "comedy": "comedy",
            "drama": "drama",
            "horror": "horror",
            "sci-fi": "sci-fi",
            "science fiction": "sci-fi",
            "romance": "romance",
            "thriller": "thriller",
        }
        target_genre = None
        for keyword, genre in genre_keywords.items():
            if keyword in query_lower:
                target_genre = genre
                break
        
        return year_range, target_genre
    
    def _filter_movies_by_constraints(
        self,
        movies: List[str],
        year_range: Optional[tuple[int, int]],
        target_genre: Optional[str]
    ) -> List[str]:
        """
        Filter movies based on year and genre constraints.
        
        :param movies: List of movie titles to filter
        :param year_range: Optional tuple of (min_year, max_year)
        :param target_genre: Optional target genre string
        :return: Filtered list of movie titles
        """
        if not self._movies:
            return movies
        
        validated_movies = []
        for movie_title in movies:
            movie_obj = next((m for m in self._movies if m.title.lower() == movie_title.lower()), None)
            if not movie_obj:
                validated_movies.append(movie_title)
                continue
            
            if year_range and movie_obj.year:
                if not (year_range[0] <= movie_obj.year <= year_range[1]):
                    continue
            
            if target_genre and movie_obj.genres:
                movie_genres = [g.lower() for g in movie_obj.genres]
                if target_genre not in movie_genres:
                    continue
            
            validated_movies.append(movie_title)
        
        return validated_movies
    
    def _calculate_validation_confidence(
        self,
        original_count: int,
        validated_count: int
    ) -> float:
        """
        Calculate confidence score based on validation results.
        
        :param original_count: Number of movies before validation
        :param validated_count: Number of movies after validation
        :return: Confidence score (0.0-1.0)
        """
        if validated_count == 0:
            return 0.3
        elif validated_count < original_count:
            return 0.7
        else:
            return 0.9
    
    def _validate_movie_results(
        self,
        movies: List[str],
        user_query: str,
        tools_used: List[str]
    ) -> tuple[List[str], float]:
        """
        Validate and filter movie results based on query constraints.
        
        :param movies: List of movie titles from tool results
        :param user_query: Original user query
        :param tools_used: List of tools that were used
        :return: Tuple of (validated_movies, confidence_score)
        """
        if not movies or "movie_search" not in tools_used:
            return movies, 1.0
        
        if not self._movies:
            return movies, 0.8
        
        year_range, target_genre = self._extract_query_constraints(user_query)
        validated_movies = self._filter_movies_by_constraints(movies, year_range, target_genre)
        confidence = self._calculate_validation_confidence(len(movies), len(validated_movies))
        
        return validated_movies, confidence
    
    def _update_answer_with_validated_movies(
        self,
        original_answer: str,
        validated_movies: List[str],
        original_movies: List[str]
    ) -> str:
        """
        Update answer text to reflect validated movies.
        
        :param original_answer: Original answer from agent
        :param validated_movies: Filtered/validated movie list
        :param original_movies: Original movie list before validation
        :return: Updated answer text
        """
        if not validated_movies:
            return (
                "I couldn't find any movies matching your specific criteria. "
                "The search results didn't match the requested year range or genre. "
                "Would you like to try a different search?"
            )
        
        if len(validated_movies) == len(original_movies):
            return original_answer
        
        if len(validated_movies) == 1:
            movies_text = validated_movies[0]
        elif len(validated_movies) == 2:
            movies_text = f"{validated_movies[0]} and {validated_movies[1]}"
        else:
            movies_text = ", ".join(validated_movies[:-1]) + f", and {validated_movies[-1]}"
        
        sentences = [s.strip() for s in original_answer.split('.') if s.strip()]
        updated_sentences = []
        found_movie_sentence = False
        
        for sentence in sentences:
            contains_original_movies = any(
                movie.lower() in sentence.lower()
                for movie in original_movies
            )
            
            if contains_original_movies and not found_movie_sentence:
                if "here are" in sentence.lower() or "movies" in sentence.lower():
                    updated_sentences.append(f"Here are the movies matching your criteria: {movies_text}.")
                else:
                    updated_sentences.append(f"Here are the matching movies: {movies_text}.")
                found_movie_sentence = True
            else:
                updated_sentences.append(sentence + ".")
        
        updated_answer = " ".join(updated_sentences)
        
        if len(validated_movies) < len(original_movies):
            filtered_count = len(original_movies) - len(validated_movies)
            updated_answer += f" (Note: {filtered_count} result(s) were filtered out as they didn't match your criteria.)"
        
        return updated_answer.strip()
    
    def _extract_quiz_data_from_answer(self, answer: str) -> Optional[Dict[str, Any]]:
        """
        Extract quiz JSON data from agent answer text.
        
        Supports two formats:
        1. [QUIZ_DATA]{...}[/QUIZ_DATA] - structured format from tool output extraction
        2. Raw JSON in answer text - fallback for legacy format
        
        :param answer: Agent answer text that may contain JSON
        :return: Parsed quiz data dictionary, or None if parsing fails
        """
        import json
        import re
        
        # Try structured format first
        structured_match = re.search(r'\[QUIZ_DATA\](.*?)\[/QUIZ_DATA\]', answer, re.DOTALL)
        if structured_match:
            try:
                return json.loads(structured_match.group(1))
            except (json.JSONDecodeError, Exception):
                logger.warning("Failed to parse structured quiz data", exc_info=True)
        
        # Fallback to raw JSON extraction
        json_match = re.search(r'\{.*\}', answer, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except (json.JSONDecodeError, Exception):
                logger.warning("Failed to parse quiz data from answer", exc_info=True)
                return None
        return None
    
    def _update_session_state(
        self,
        session_state,
        tools_used: List[str],
        result: Dict[str, Any]
    ) -> None:
        """
        Update session state based on tools used and results.
        
        :param session_state: SessionState instance
        :param tools_used: List of tools that were used
        :param result: Agent result dictionary
        """
        quiz_state = session_state.get_quiz_state()
        
        if "generate_movie_quiz" in tools_used:
            # Try to get quiz_data directly from result (preferred)
            quiz_data = result.get("quiz_data")
            if not quiz_data:
                # Fallback: extract from answer text
                answer = result.get("answer", "")
                quiz_data = self._extract_quiz_data_from_answer(answer)
            
            if quiz_data:
                # Use controller to activate quiz (controller owns state management)
                quiz_controller = QuizController(quiz_state)
                quiz_controller.activate_quiz(quiz_data)
                logger.info(f"✅ Quiz activated: {len(quiz_data.get('questions', []))} questions, session: {id(session_state)}")
            else:
                quiz_state.activate({})
        
        # REMOVED: check_quiz_answer handling from _update_session_state
        # Quiz answers are now handled by QuizController in chat() method
        # The controller owns quiz state progression - no LLM involvement
        # This prevents the agent from making unreliable decisions about quiz progression
        
        if result.get("quiz_completed", False):
            quiz_state.deactivate()
    
    def _handle_tool_failure(
        self,
        user_message: str,
        error_message: str,
        latency_ms: int,
        session_id: str
    ) -> ChatResponse:
        """
        Handle tool failure with graceful fallback.
        
        :param user_message: Original user message
        :param error_message: Error message from tool/agent
        :param latency_ms: Latency in milliseconds
        :param session_id: Session ID
        :return: ChatResponse with graceful error message
        """
        logger.warning(f"Tool failure handled gracefully - Error: {error_message}")
        
        answer = (
            "I encountered an issue processing your request. "
            "This might be due to a temporary service limitation. "
            "Could you try rephrasing your question or asking about something else?"
        )
        
        response = ChatResponse(
            answer=answer,
            movies=[],
            tools_used=[],
            llm_latency_ms=0,
            tool_latency_ms=0,
            latency_ms=latency_ms,
            reasoning_type="error_handling",
            confidence=0.0
        )
        
        if self._session_memory:
            self._session_memory.record(session_id, {
                "type": "assistant_response",
                "content": answer,
                "role": "assistant",
                "error": error_message,
            })
        
        return response
    
    def _handle_partial_results(
        self,
        result: Dict[str, Any],
        user_message: str,
        session_id: str
    ) -> Dict[str, Any]:
        """
        Handle partial or empty tool results with fallback strategies.
        
        :param result: Agent result dictionary
        :param user_message: Original user message
        :param session_id: Session ID
        :return: Potentially modified result dictionary
        """
        tools_used = result.get("tools_used", [])
        movies = result.get("movies", [])
        answer = result.get("answer", "")
        
        if tools_used and not movies and "movie_search" in tools_used:
            logger.info("Tool returned empty results - applying fallback strategy")
            if "couldn't find" not in answer.lower() and "no results" not in answer.lower():
                result["answer"] = (
                    f"{answer}\n\n"
                    "I couldn't find a strong match for your query. "
                    "Would you like to widen the search criteria or try a different approach?"
                )
            result["confidence"] = 0.3
        
        elif movies and result.get("confidence", 1.0) < 0.8:
            logger.info("Partial constraint match detected - enhancing answer")
            if ("couldn't find" not in answer.lower() and 
                "no results" not in answer.lower() and
                "close matches" not in answer.lower() and
                "These are" not in answer):
                result["answer"] = (
                    f"{answer}\n\n"
                    "Note: Some results may not perfectly match all your criteria, "
                    "but they're the closest matches I found."
                )
        
        return result
    
    def clear_memory(self, session_id: Optional[str] = None) -> None:
        """
        Clear memory for a specific session or all sessions.
        
        :param session_id: Session ID to clear (if None, clears all sessions)
        """
        if self._session_memory:
            if session_id:
                self._session_memory.clear_session(session_id)
            else:
                self._session_memory.clear_all()
        
        if session_id:
            self._session_context.clear_context(session_id)
        else:
            self._session_context.clear_all()