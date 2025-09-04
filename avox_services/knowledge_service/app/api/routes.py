from http.client import HTTPException

from fastapi import APIRouter
from pydantic import BaseModel

from avox_shared.knowledge_service.document import DocumentIngestRequest, DocumentIngestResponse
from avox_shared.knowledge_service.rag import RAGQuery, RAGResponse
from knowledge_service.app.deps import RAGPipelineDep, RAGUserDep, RAGDocumentIngestor

router = APIRouter(prefix="/rag", tags=["RAG Operations"])

@router.post("/ingest-documents", response_model=DocumentIngestResponse)
def ingest_documents(
    req: DocumentIngestRequest,
    current_user: RAGUserDep,
    ingestor: RAGDocumentIngestor,
):
    result: DocumentIngestResponse

    if not current_user or not current_user.company_id:
        raise HTTPException(status_code=400, detail="Invalid user context")

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
    rag_query: RAGQuery,
    pipeline: RAGPipelineDep,
    current_user: RAGUserDep,
):

    if not current_user or not current_user.company_id:
        raise HTTPException(status_code=400, detail="Invalid user context")

    return pipeline.iterative_answer(user=current_user, doc_ids=rag_query.doc_ids, question=rag_query.question);

class HealthResponse(BaseModel):
    status: str

@router.get("/health", response_model=HealthResponse)
def health_check():
    """
    Проверка состояния сервиса.
    """
    return {"status": "ok"}