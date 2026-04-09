from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import DATABASE_URL

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_session():
    return SessionLocal()


def create_tables():
    from app.models.job import Job
    from app.models.report import Report
    Base.metadata.create_all(bind=engine)