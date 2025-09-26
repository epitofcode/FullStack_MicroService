from pydantic import BaseModel, EmailStr, UUID4
from uuid import UUID
from datetime import datetime
from typing import List

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class OTPSchema(BaseModel):
    email: EmailStr
    otp: str

class APIKeyCreateRequest(BaseModel):
    user_id: UUID4

class APIKeyCreateOut(BaseModel):
    id: UUID4
    plain_key: str
    key_prefix: str
    user_id: UUID4
    created_at: datetime
    message: str = "Please save this key securely. You will not be able to see it again."
    class Config:
        from_attributes = True
        
class APIKeyInfoOut(BaseModel):
    id: UUID4
    key_prefix: str
    user_id: UUID4
    created_at: datetime
    is_active: bool
    class Config:
        from_attributes = True

class APIKeyValidateRequest(BaseModel):
    plain_key: str

class APIKeyValidateOut(BaseModel):
    user_id: UUID4
    is_active: bool
    class Config:
        from_attributes = True