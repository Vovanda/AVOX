import uuid

from sqlalchemy import Column, Boolean, ForeignKey, Enum, DateTime
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship

from knowledge_service.app.models.base import Base, TimestampMixin
from knowledge_service.app.models.enums import DocAccessRole


class AccessGrant(Base, TimestampMixin):
    __tablename__ = 'access_grants'

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(PG_UUID(as_uuid=True), ForeignKey('documents.id', ondelete="CASCADE"), nullable=False)
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    access_role = Column(Enum(DocAccessRole), default=DocAccessRole.UNKNOWN, nullable=False)  # view/edit/manage
    is_revoked = Column(Boolean, default=False)
    expires_at = Column(DateTime, nullable=True)

    # Связи
    document = relationship("Document", back_populates="access_grants")
    user = relationship("User", back_populates="access_grants")