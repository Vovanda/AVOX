import uuid

from sqlalchemy import Column, String, ForeignKey, Enum, DateTime, Index
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship

from knowledge_service.app.models.base import Base, TimestampMixin
from knowledge_service.app.models.enums import UserType, UserRole, AuthProvider


class Company(Base, TimestampMixin):
    __tablename__ = 'companies'
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)

    # Связи
    users = relationship("User", back_populates="company", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="company")

class User(Base, TimestampMixin):
    __tablename__ = 'users'
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    external_id = Column(String(255), nullable=True) # Уникальный только с provider!
    provider = Column(Enum(AuthProvider), default=AuthProvider.INTERNAL, nullable=False)
    company_id = Column(PG_UUID(as_uuid=True), ForeignKey('companies.id', ondelete="CASCADE"))
    user_type = Column(Enum(UserType), default=UserType.UNKNOWN, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.BASE, nullable=False)
    last_login = Column(DateTime, nullable=True)

    #Связи
    company = relationship("Company", back_populates="users")
    access_grants = relationship("AccessGrant", back_populates="user", cascade="all, delete-orphan")
    created_documents = relationship("Document", back_populates="owner")  # Связь с документами

    __table_args__ = (
        Index('idx_user_company_role', 'company_id', 'role'),
        Index('uq_provider_external', 'provider', 'external_id', unique=True),
    )