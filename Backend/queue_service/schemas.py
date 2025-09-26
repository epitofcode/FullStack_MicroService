from pydantic import BaseModel, UUID4, AnyHttpUrl
from datetime import datetime
from typing import Dict, Any, Optional

class UploadInitiationIn(BaseModel):
    filename: str
    workflow_type: Optional[str] = None
    model_identifier: Optional[str] = None

class UploadInitiationOut(BaseModel):
    job_id: UUID4
    upload_url: AnyHttpUrl

class JobOut(BaseModel):
    id: UUID4
    user_id: UUID4
    status: str
    created_at: datetime
    class Config:
        from_attributes = True