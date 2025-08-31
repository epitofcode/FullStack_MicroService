from pydantic import BaseModel, HttpUrl
from uuid import UUID
from datetime import datetime
from typing import Optional

# NO LONGER NEEDED: from .database import Base

class JobCreate(BaseModel):
    model_identifier: str
    input_url: HttpUrl

class JobOut(BaseModel):
    id: UUID
    user_id: UUID
    model_identifier: str
    status: str
    input_url: HttpUrl
    output_url: Optional[HttpUrl] = None
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True