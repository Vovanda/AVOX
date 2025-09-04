from fastapi import APIRouter, HTTPException

from api_gateway.app.deps import HttpClientDep, AuthTokenDep, KNOWLEDGE_SERVICE_URL
from avox_shared.knowledge_service.document import DocumentIngestRequest
from avox_shared.knowledge_service.rag import RAGQuery

router = APIRouter(prefix="/api/rag", tags=["RAG Gateway"])

@router.post("/ingest-documents")
async def ingest_documents(
    req: DocumentIngestRequest,
    client: HttpClientDep,
    token: AuthTokenDep,
):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    try:
        resp = await client.post(
            f"{KNOWLEDGE_SERVICE_URL}/rag/ingest-documents",
            json=req.model_dump(),
            headers=headers,
        )
        if resp.status_code >= 400:
            raise HTTPException(status_code=resp.status_code, detail=resp.text)
        return resp.json()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Gateway error: {e}")

@router.post("/query")
async def query_single_document(
    req: RAGQuery,
    client: HttpClientDep,
    token: AuthTokenDep,
):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    resp = await client.post(
        f"{KNOWLEDGE_SERVICE_URL}/rag/query",
        json=req.model_dump(),
        headers=headers,
    )
    if resp.status_code >= 400:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()