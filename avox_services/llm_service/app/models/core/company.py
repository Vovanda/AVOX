import uuid

from sqlalchemy import Column, String, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship

from llm_service.app.models.base import Base, TimestampMixin
from llm_service.app.models.enums import RoleType


class Company(Base, TimestampMixin):
    __tablename__ = 'companies'
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    users = relationship("User", back_populates="company")

class User(Base, TimestampMixin):
    __tablename__ = 'users'
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vk_id = Column(String(255), unique=True, nullable=True)
    company_id = Column(PG_UUID(as_uuid=True), ForeignKey('companies.id'))
    role = Column(Enum(RoleType), nullable=False)
    company = relationship("Company", back_populates="users")