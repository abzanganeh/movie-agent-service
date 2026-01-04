from typing import Any, List, Optional
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatResult, ChatGeneration


class DummyChatModel(BaseChatModel):
    """LangChain-compatible dummy chat model for evaluation (no tool calls)."""

    @property
    def _llm_type(self) -> str:
        return "dummy-chat"

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any,
    ) -> ChatResult:
        # Always return a simple message; no tool_calls emitted.
        generation = ChatGeneration(message=AIMessage(content="Dummy response"))
        return ChatResult(generations=[generation])

    async def _agenerate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any,
    ) -> ChatResult:
        return self._generate(messages, stop=stop, run_manager=run_manager, **kwargs)

    def bind(self, **kwargs: Any):
        # Support bind_tools() compatibility; return self unchanged.
        return self
