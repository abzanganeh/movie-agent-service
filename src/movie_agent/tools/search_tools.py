from typing import Any
from pydantic import BaseModel, Field
from langchain.tools import BaseTool
from langchain_core.documents import Document

from .retriever_tool import RetrieverTool


class SearchActorArgs(BaseModel):
    actor: str = Field(description="Actor name to search for")


class SearchDirectorArgs(BaseModel):
    director: str = Field(description="Director name to search for")


class SearchYearArgs(BaseModel):
    year: str = Field(description="Release year to search for (string or int)")


class _BaseSearchTool(BaseTool):
    """Shared logic for actor/director/year search tools."""

    retriever: Any = Field(default=None)
    top_k: int = Field(default=5)

    def __init__(self, retriever: RetrieverTool, top_k: int = 5, **kwargs):
        super().__init__(**kwargs)
        self.retriever = retriever
        self.top_k = int(top_k)

    def _query(self, query: str) -> str:
        docs: list[Document] = self.retriever.retrieve(query, k=self.top_k)
        if not docs:
            return "No results found."
        summaries = [
            f"{doc.metadata.get('title', 'Unknown')} ({doc.metadata.get('year', 'N/A')})"
            for doc in docs
        ]
        return "; ".join(summaries)

    async def _arun(self, *args, **kwargs) -> str:
        return self._run(*args, **kwargs)


class SearchActorTool(_BaseSearchTool):
    name: str = "search_actor"
    description: str = "Find movies featuring a given actor."
    args_schema: type[BaseModel] = SearchActorArgs

    def _run(self, actor: str) -> str:
        return self._query(f"actor: {actor}")


class SearchDirectorTool(_BaseSearchTool):
    name: str = "search_director"
    description: str = "Find movies directed by a given director."
    args_schema: type[BaseModel] = SearchDirectorArgs

    def _run(self, director: str) -> str:
        return self._query(f"director: {director}")


class SearchYearTool(_BaseSearchTool):
    name: str = "search_year"
    description: str = "Find movies released in a given year."
    args_schema: type[BaseModel] = SearchYearArgs

    def _run(self, year: str) -> str:
        return self._query(f"year: {year}")

