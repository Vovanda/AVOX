# AVOX\avox_services\knowledge_service\app\deps.py

from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from knowledge_service.app.core import config
from knowledge_service.app.db.session import get_db
from knowledge_service.app.llm.base_provider import BaseLLMProvider
from knowledge_service.app.llm.provider_factory import get_llm_provider
from knowledge_service.app.llm.rag_pipeline import KnowledgeRAGPipeline
from knowledge_service.app.models.core.company import User
from knowledge_service.app.services import DocumentIngestor
from knowledge_service.app.services.auth import get_current_active_user


def get_document_ingestor(db: Session = Depends(get_db)) -> DocumentIngestor:
    return DocumentIngestor(db)

def get_llm() -> BaseLLMProvider:
    return get_llm_provider(provider=config.LLM_PROVIDER)

def get_rag_pipeline(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
    llm: Annotated[BaseLLMProvider, Depends(get_llm)],
) -> KnowledgeRAGPipeline:
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive users cannot access knowledge services"
        )
    return KnowledgeRAGPipeline(db_session=db, llm_provider=llm)


# Type annotations for common dependency combinations
LLMDep = Annotated[BaseLLMProvider, Depends(get_llm)]
RAGUserDep = Annotated[User, Depends(get_current_active_user)]
RAGPipelineDep = Annotated[KnowledgeRAGPipeline, Depends(get_rag_pipeline)]
RAGDocumentIngestor = Annotated[DocumentIngestor, Depends(get_document_ingestor)]
