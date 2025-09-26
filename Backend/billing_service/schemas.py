from pydantic import BaseModel, UUID4
from datetime import datetime
from typing import Optional

class UserBalanceOut(BaseModel):
    user_id: UUID4
    balance: int
    updated_at: datetime
    class Config:
        from_attributes = True

class CreditActionRequest(BaseModel):
    user_id: UUID4
    model_identifier: str

class PaymentRequest(BaseModel):
    amount: int
    name: str
    email: str
    phone: Optional[str] = None
    user_id: UUID4