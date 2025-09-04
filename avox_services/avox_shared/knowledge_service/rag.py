from typing import List, Optional

from pydantic import BaseModel


class RAGQuery(BaseModel):
    """Request model for RAG queries"""
    question: str
    doc_ids: Optional[List[str]] = None

class RAGResponse(BaseModel):
    """Response model for RAG queries"""
    final_result: str
    facts: List[Fact]
    reasoning: str
    used_documents: List[str]
    used_doc_chunks: List[str]
    confidence: float
    llm_provider: str
    processing_time_ms: int
    warnings: List[str] = []
    truncated: bool = False
