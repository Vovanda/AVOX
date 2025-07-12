from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from knowledge_service.app.core.config import DATABASE_URL

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Session:
    """
    FastAPI dependency: yields a SQLAlchemy session and ensures it's closed.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
