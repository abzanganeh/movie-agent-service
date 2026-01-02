from langchain_core.language_models import BaseLanguageModel
from typing import Any, List, Optional

class DummyLLM(BaseLanguageModel):
    """LangChain-compatible dummy LLM for evaluation."""

    @property
    def _llm_type(self) -> str:
        return "dummy"

    def _call(self, prompt: str, stop: Optional[List[str]] = None) -> str:
        return f"Dummy LLM response to: {prompt}"

    async def _acall(self, prompt: str, stop: Optional[List[str]] = None) -> str:
        return f"Dummy async response to: {prompt}"

    # Required abstract methods
    def predict(self, prompt: str, stop: Optional[List[str]] = None) -> str:
        return self._call(prompt, stop=stop)

    async def apredict(self, prompt: str, stop: Optional[List[str]] = None) -> str:
        return await self._acall(prompt, stop=stop)

    def generate_prompt(self, prompt: Any, stop: Optional[List[str]] = None) -> str:
        return str(prompt)

    async def agenerate_prompt(self, prompt: Any, stop: Optional[List[str]] = None) -> str:
        return str(prompt)

    def predict_messages(self, messages: Any, stop: Optional[List[str]] = None) -> str:
        return "Dummy response"

    async def apredict_messages(self, messages: Any, stop: Optional[List[str]] = None) -> str:
        return "Dummy async response"

    def invoke(self, prompt: str, stop: Optional[List[str]] = None) -> str:
        return self._call(prompt, stop)

    async def ainvoke(self, prompt: str, stop: Optional[List[str]] = None) -> str:
        return await self._acall(prompt, stop)

    def bind(self, **kwargs: Any):
        return self
