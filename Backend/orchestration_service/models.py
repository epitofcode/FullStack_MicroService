from sqlalchemy import Column, String, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID as UUIDType
from .database import Base

class Job(Base):
    __tablename__ = 'jobs'
    id = Column(UUIDType(as_uuid=True), primary_key=True)
    user_id = Column(UUIDType(as_uuid=True))
    model_identifier = Column(String)
    workflow_type = Column(String)
    blob_name = Column(String)
    status = Column(String)
    input_data = Column(JSON)
    result_data = Column(JSON)
    error_message = Column(String)
    created_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    __table_args__ = {'extend_existing': True}
