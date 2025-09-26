from sqlalchemy import Column, String, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime, timezone
from .database import Base

class Job(Base):
    __tablename__ = "jobs"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), index=True, nullable=False)
    model_identifier = Column(String, nullable=True)
    workflow_type = Column(String, nullable=True, index=True)
    blob_name = Column(String, nullable=True)
    status = Column(String, nullable=False, default='AWAITING_UPLOAD')
    input_data = Column(JSON, nullable=False)
    result_data = Column(JSON, nullable=True)
    error_message = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime(timezone=True), nullable=True)