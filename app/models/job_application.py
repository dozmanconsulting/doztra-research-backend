import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, JSON

from app.db.base_class import Base


class JobApplication(Base):
    __tablename__ = "job_applications"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    email = Column(String, nullable=False, index=True)
    role = Column(String, nullable=False, index=True)
    linkedin = Column(String, nullable=True)
    portfolio = Column(String, nullable=True)
    resume_path = Column(String, nullable=True)
    cover_letter = Column(Text, nullable=True)
    status = Column(String, nullable=False, default="submitted")
    extra_data = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
