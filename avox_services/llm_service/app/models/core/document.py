import uuid

from sqlalchemy import Column, Enum, ForeignKey, Text, String, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship

from llm_service.app.models.base import Base, TimestampMixin
from llm_service.app.models.enums import SourceType, AccessLevel


class Document(Base, TimestampMixin):
    __tablename__ = 'documents'
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(PG_UUID(as_uuid=True), ForeignKey('companies.id'))
    owner_id = Column(PG_UUID(as_uuid=True), ForeignKey('users.id'))
    source_type = Column(Enum(SourceType), nullable=False)
    title = Column(String(length=512), nullable=False)
    access_level = Column(Enum(AccessLevel), nullable=False)
    is_hot = Column(Boolean, default=False)

    chunks = relationship("DocumentChunk", back_populates="document")

class DocumentChunk(Base, TimestampMixin):
    __tablename__ = 'document_chunks'
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(PG_UUID(as_uuid=True), ForeignKey('documents.id'))
    is_important = Column(Boolean, default=False)
    chunk_text = Column(Text, nullable=False)
    chunk_idx = Column(Integer, nullable=False)

    document = relationship("Document", back_populates="chunks")