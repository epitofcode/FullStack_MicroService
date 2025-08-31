from pydantic import BaseModel
from uuid import UUID
from datetime import datetime

class UserBalanceOut(BaseModel):
    user_id: UUID
    balance: int
    updated_at: datetime
    
    class Config:
        from_attributes = True

class CreditPolicyOut(BaseModel):
    model_identifier: str
    credits_per_unit: int
    unit_description: str

    class Config:
        from_attributes = True