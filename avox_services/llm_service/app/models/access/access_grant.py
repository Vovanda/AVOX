import uuid

from sqlalchemy import Column, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from llm_service.app.models.base import Base, TimestampMixin


class AccessGrant(Base, TimestampMixin):
    __tablename__ = 'access_grants'
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(PG_UUID(as_uuid=True), ForeignKey('documents.id'))
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey('users.id'))
    can_edit = Column(Boolean, default=False)
    can_read = Column(Boolean, default=False)