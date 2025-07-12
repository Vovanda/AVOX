import uuid
from datetime import datetime
from typing import Optional

from pgvector.sqlalchemy import Vector
from sqlalchemy import or_, Column, Enum, ForeignKey, Text, String, Boolean, Integer, Index, DateTime
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship, validates

from knowledge_service.app.models import Base, AccessGrant, User, TimestampMixin
from knowledge_service.app.models.enums import DocAccessLevel, SourceType, UserType, EmbeddingStatus


class Document(Base, TimestampMixin):
    __tablename__ = 'documents'

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
                comment="Уникальный идентификатор документа")
    company_id = Column(PG_UUID(as_uuid=True), ForeignKey('companies.id', ondelete="CASCADE"), nullable=False,
                comment="Компания, которой принадлежит документ")
    owner_id = Column(PG_UUID(as_uuid=True), ForeignKey('users.id', ondelete="SET NULL"), nullable=True, index=True,
                comment="Владелец (создатель) документа")
    source_type = Column(Enum(SourceType), nullable=False, comment="Источник: FILE, TEXT, URL, CHAT, API и др.")
    title = Column(String(length=512), nullable=False, index=True, comment="Название документа")
    access_level = Column(Enum(DocAccessLevel), nullable=False, default=DocAccessLevel.RESTRICTED,
                comment="Уровень доступа: PUBLIC, INTERNAL, RESTRICTED")
    is_hot = Column(Boolean, default=False, index=True, comment="Является ли актуальным")
    is_approved = Column(Boolean, default=False, index=True, comment="Одобрен ли документ")
    last_accessed_at = Column(DateTime, nullable=True, comment="Время последнего доступа")

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
    owner = relationship("User", back_populates="created_documents")

    @validates('access_level')
    def validate_access_level(self, key, value):
        if value == DocAccessLevel.PUBLIC and not self.is_approved:
            raise ValueError("Public documents must be approved")
        return value

    def get_effective_access(self, user: Optional[User]) -> bool:
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

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
                comment="Уникальный идентификатор части документа")
    document_id = Column(PG_UUID(as_uuid=True), ForeignKey('documents.id', ondelete="CASCADE"), nullable=False,
                comment="Документ, к которому относится часть")
    is_hot = Column(Boolean, default=False, index=True, comment="Является ли актуальной (важной) частью")
    chunk_text = Column(Text, nullable=False, comment="Текст фрагмента")
    chunk_idx = Column(Integer, nullable=False, comment="Позиция части в документе")
    chunk_scope = Column(String(64), nullable=True, comment="Единица разбиения чанка: symbols, words, sentence")
    overlap = Column(Integer, nullable=False, default=0, comment="Количество перекрывающихся единиц (слов, предложений и т.п.) между чанками")
    # Связи
    document = relationship("Document", back_populates="chunks")
    embeddings = relationship("ChunkEmbedding384", back_populates="chunk", cascade="all, delete-orphan")

    __table_args__ = (
        Index('ix_chunk_document_idx', 'document_id', 'chunk_idx', unique=True)
    ),

    @property
    def document_metadata (self):
        return {
            'document_id': str(self.document_id),
            'is_hot': self.is_hot,
            'position': self.chunk_idx
        }

class ChunkEmbedding384(Base, TimestampMixin):
    __tablename__ = 'chunk_embeddings_384'
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, comment="Уникальный идентификатор эмбеддинга")
    chunk_id = Column(PG_UUID(as_uuid=True), ForeignKey('document_chunks.id', ondelete="CASCADE"), nullable=False, comment="Фрагмент, к которому относится эмбеддинг")
    vector = Column(Vector(384), nullable=False, comment="Эмбеддинг вектора (use cosine; ivfflat(lists=100))")
    embedding_scope = Column(String(64), nullable=False, default="chunk", comment="Область эмбеддинга: chunk, subchunk и др.")
    subchunk_idx = Column(Integer, nullable=False, default=0, comment="Порядковый номер подчанка внутри фрагмента")
    embedding_model = Column(String(length=255), nullable=False, index=True, comment="Название модели эмбеддинга")
    overlap = Column(Integer, nullable=False, default=0, comment="Количество перекрывающихся единиц (слов, токенов и т.п.) между подчанками")
    status = Column(Enum(EmbeddingStatus), nullable=False, default=EmbeddingStatus.PENDING, comment="Статус эмбеддинга: pending, processing, completed, completed")
    attempts = Column(Integer, default=0, nullable=False, comment="Количество попыток обработки")
    error_message = Column(Text, nullable=True, comment="Сообщение об ошибке при обработке эмбеддинга")

    # Связи
    chunk = relationship("DocumentChunk", back_populates="embeddings")

    __table_args__ = (
        Index(
            'ix_chunk_vector_cosine',
            'vector',
            postgresql_using='ivfflat',
            postgresql_ops={'vector': 'vector_cosine_ops'},
            postgresql_with={"lists": 100}
        ),
    )