import uuid

from fastapi import APIRouter, Depends

from knowledge_service.app.api.schemas.document import DocumentIngestRequest, DocumentIngestResponse
from knowledge_service.app.api.schemas.rag import RAGQuery, RAGResponse
from knowledge_service.app.deps import RAGPipelineDep, RAGUserDep, get_document_ingestor
from knowledge_service.app.llm.rag_pipeline import KnowledgeRAGPipeline
from knowledge_service.app.models.core.company import User
from knowledge_service.app.services.document_ingestor import DocumentIngestor

router = APIRouter(prefix="/rag", tags=["RAG Operations"])

@router.post("/ingest-documents", response_model=DocumentIngestResponse)
def ingest_documents(
    req: DocumentIngestRequest,
    current_user: User = Depends(RAGUserDep),
    ingestor: DocumentIngestor = Depends(get_document_ingestor),
):
    result: DocumentIngestResponse

    try:
        result = ingestor.ingest(
            text=req.text,
            title=req.title,
            company_id=current_user.company_id,
            owner_id=current_user.id,
            source_type=req.source_type,
            access_level=req.access_level,
        )
    except Exception as e:
        result = DocumentIngestResponse(
            document_id=None,
            title=req.title,
            status="failed",
            error=str(e)
        )

    return result

@router.post("/query", response_model=RAGResponse)
def query(
    question: str,
    pipeline: KnowledgeRAGPipeline = Depends(RAGPipelineDep),
    current_user: User = Depends(RAGUserDep),
):
    return pipeline.iterative_answer(user=current_user, question=question)


@router.post("/documents/{doc_id}/query", response_model=RAGResponse)
def query_single_document(
    doc_id: uuid.UUID,
    query: RAGQuery,
    pipeline: KnowledgeRAGPipeline = Depends(RAGPipelineDep),
    current_user: User = Depends(RAGUserDep),
):
    """Поиск по конкретному документу по его UUID"""
    return pipeline.iterative_answer(question=query.question, doc_ids=[doc_id], user=current_user)


@router.get("/health", tags=["Health"])
def health_check():
    """
    Проверка состояния сервиса.
    """
    return {"status": "ok"}
