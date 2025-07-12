
# AVOX\avox_services\knowledge_service\app\api\schemas\rag.py
from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel


class FactCertainty(str, Enum):
    CONFIRMED = "confirmed"
    LIKELY = "likely"
    CONTRADICTS = "contradicts"

class Fact(BaseModel):
    """Verified fact extracted from documents"""
    text: str
    certainty: FactCertainty
    reasoning: str
    source_doc_id: str
    source_doc_chuk_id: str
    timestamp: datetime = datetime.now()

class RAGQuery(BaseModel):
    """Request model for RAG queries"""
    question: str
    doc_ids: Optional[List[str]] = None
    temperature: float = 0.7
    max_facts: int = 5
    min_confidence: float = 0.5
    include_sources: bool = True

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
