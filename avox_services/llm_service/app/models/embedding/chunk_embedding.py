import uuid

from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from llm_service.app.models.base import Base, TimestampMixin
from llm_service.app.models.enums import EmbeddingStatus


class ChunkEmbedding(Base, TimestampMixin):
    __tablename__ = 'chunk_embeddings'
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chunk_id = Column(PG_UUID(as_uuid=True), ForeignKey('document_chunks.id'))
    vector = Column(Vector(512))  # Размерность модели
    status = Column(Enum(EmbeddingStatus), default='pending')