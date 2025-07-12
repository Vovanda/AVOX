# knowledge_service/app/api/schemas/document.py
import uuid
from typing import Optional

from pydantic import BaseModel, Field

from knowledge_service.app.models.enums import DocAccessLevel, SourceType


class DocumentIngestRequest(BaseModel):
    text: str = Field(..., description="Текст для инжеста")
    title: str = Field(..., description="Заголовок документа")
    source_type: SourceType = Field(..., description="Тип источника")
    access_level: DocAccessLevel = Field(..., description="Уровень доступа")

class DocumentIngestResponse(BaseModel):
    document_id: Optional[uuid.UUID] = Field(None, description="UUID созданного документа")
    title: str = Field(..., description="Заголовок")
    status: str = Field(..., description="success / failed")
    error: Optional[str] = Field(None, description="Описание ошибки, если есть")
