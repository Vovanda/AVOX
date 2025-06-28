import uuid
from datetime import datetime
from typing import Optional

from pgvector.sqlalchemy import Vector
from sqlalchemy import or_, Column, Enum, ForeignKey, Text, String, Boolean, Integer, Index, DateTime
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship, validates

from knowledge_service.app.models import Base, AccessGrant, TimestampMixin
from knowledge_service.app.models.enums import DocAccessLevel, SourceType, UserType, EmbeddingStatus


class Document(Base, TimestampMixin):
    __tablename__ = 'documents'

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(PG_UUID(as_uuid=True), ForeignKey('companies.id', ondelete="CASCADE"),
                        nullable=False)
    owner_id = Column(PG_UUID(as_uuid=True), ForeignKey('users.id', ondelete="SET NULL"),
                      nullable=True)
    source_type = Column(Enum(SourceType), nullable=False)
    title = Column(String(length=512), nullable=False, index=True)
    access_level = Column(Enum(DocAccessLevel), nullable=False, default=DocAccessLevel.RESTRICTED)
    is_hot = Column(Boolean, default=False, index=True)
    is_approved = Column(Boolean, default=False, index=True)
    last_accessed_at = Column(DateTime, nullable=True)

    # Связи
    chunks = relationship(
        "DocumentChunk",
        back_populates="document",
        cascade="all, delete-orphan",
        order_by="DocumentChunk.chunk_idx"
    )

    access_grants = relationship(
        "AccessGrant",
        back_populates="document",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )

    company = relationship("Company", back_populates="documents")

    __table_args__ = (
        Index('ix_document_owner_company', 'owner_id', 'company_id'),
        Index('ix_document_access_level', 'access_level', 'is_approved'),
    )
    owner = relationship("User", back_populates="created_documents")

    @validates('access_level')
    def validate_access_level(self, key, value):
        if value == DocAccessLevel.PUBLIC and not self.is_approved:
            raise ValueError("Public documents must be approved")
        return value

    def get_effective_access(self, user: Optional['User']) -> bool:
        """Проверка доступа к документу"""
        if self.access_level == DocAccessLevel.PUBLIC:
            return self.is_approved and (user is None or user.company_id == self.company_id)

        if user is None:
            return False

        if user.id == self.owner_id:
            return True

        if self.access_level == DocAccessLevel.INTERNAL:
            return (
                    user.user_type == UserType.INTERNAL and
                    user.company_id == self.company_id
            )

        return self.access_grants.filter(
            AccessGrant.user_id == user.id,
            AccessGrant.is_revoked == False,
            or_(
                AccessGrant.expires_at == None,
                AccessGrant.expires_at >= datetime.now()
            )
        ).first() is not None

class DocumentChunk(Base, TimestampMixin):
    __tablename__ = 'document_chunks'

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(PG_UUID(as_uuid=True), ForeignKey('documents.id', ondelete="CASCADE"), nullable=False)
    is_important = Column(Boolean, default=False, index=True)
    chunk_text = Column(Text, nullable=False)
    chunk_idx = Column(Integer, nullable=False)
    vector = Column(Vector(384))

    # Связи
    document = relationship("Document", back_populates="chunks")
    embeddings = relationship("ChunkEmbedding", back_populates="chunk", cascade="all, delete-orphan")

    __table_args__ = (
        Index('ix_chunk_document_idx', 'document_id', 'chunk_idx', unique=True),
        Index('ix_chunk_important', 'document_id', 'is_important'),
    )

    @property
    def document_metadata (self):
        return {
            'document_id': str(self.document_id),
            'is_important': self.is_important,
            'position': self.chunk_idx
        }

class ChunkEmbedding(Base, TimestampMixin):
    __tablename__ = 'chunk_embeddings'
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chunk_id = Column(PG_UUID(as_uuid=True), ForeignKey('document_chunks.id', ondelete="CASCADE"), nullable=False)
    vector = Column(Vector(512))
    status = Column(Enum(EmbeddingStatus), default=EmbeddingStatus.PENDING)

    # Связи
    chunk = relationship("DocumentChunk", back_populates="embeddings")