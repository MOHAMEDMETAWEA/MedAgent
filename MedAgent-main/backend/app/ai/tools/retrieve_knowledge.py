"""Tool: retrieve_medical_knowledge — RAG search for the agent."""

from typing import Any

from pydantic import BaseModel, Field

from app.ai.agent.base import Tool
from app.ai.retrieval.retriever import Retriever


class RetrieverInput(BaseModel):
    """Input schema for medical knowledge retrieval."""

    query: str = Field(
        min_length=1,
        description="The medical question to search for in the knowledge base",
    )
    language: str = Field(
        default="en",
        pattern="^(ar|en)$",
        description="Language filter: 'ar' or 'en'",
    )
    top_k: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Number of top results to return (1-20)",
    )


class RetrieveKnowledgeTool(Tool):
    """Searches the medical knowledge base and returns top chunks with citations."""

    def __init__(self, retriever: Retriever):
        self._retriever = retriever

    @property
    def name(self) -> str:
        return "retrieve_medical_knowledge"

    @property
    def description(self) -> str:
        return (
            "Search the medical knowledge base for evidence-based guidelines, "
            "clinical information, and triage protocols. Returns relevant text "
            "chunks with source citations and URLs."
        )

    @property
    def input_schema(self) -> type[BaseModel]:
        return RetrieverInput

    async def run(self, input_data: BaseModel) -> dict[str, Any]:

        if not isinstance(input_data, RetrieverInput):
            raise TypeError(f"Expected RetrieverInput, got {type(input_data)}")

        results = await self._retriever.search(
            query=input_data.query,
            language=input_data.language,
            top_k=input_data.top_k,
        )

        chunks = []
        for r in results:
            chunks.append(
                {
                    "source": r["source"],
                    "title": r.get("section_title", ""),
                    "url": r.get("source_url", ""),
                    "content_excerpt": r["content"][:300],
                    "similarity": round(r["similarity"], 3),
                }
            )

        return {
            "query": input_data.query,
            "total_results": len(chunks),
            "chunks": chunks,
        }
