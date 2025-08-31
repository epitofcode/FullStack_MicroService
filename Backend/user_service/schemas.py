from pydantic import BaseModel, EmailStr
from uuid import UUID
from datetime import datetime

# --- Pydantic models for data validation ---

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: UUID
    email: EmailStr
    created_at: datetime

    class Config:
        from_attributes = True # Replaces orm_mode = True in Pydantic v2

class Token(BaseModel):
    access_token: str
    token_type: str