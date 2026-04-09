import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text
from app.core.database import Base


class Report(Base):
    __tablename__ = "reports"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String, nullable=False)
    components = Column(Text, nullable=True)
    risks = Column(Text, nullable=True)
    recommendations = Column(Text, nullable=True)
    raw_response = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)