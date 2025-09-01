from sqlalchemy import Column, String, Integer, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from database import Base
from datetime import datetime
import uuid

class CreditPolicy(Base):
    __tablename__ = "credit_policies"
    id = Column(Integer, primary_key=True, index=True)
    model_identifier = Column(String, unique=True, index=True, nullable=False)
    credits_per_unit = Column(Integer, nullable=False)
    unit_description = Column(String, default="per 30 seconds")
    is_active = Column(Boolean, default=True)

class UserBalance(Base):
    __tablename__ = "user_balances"
    user_id = Column(UUID(as_uuid=True), primary_key=True)
    balance = Column(Integer, nullable=False, default=100) # Default set to 100 free credits
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    amount = Column(Integer, nullable=False)
    description = Column(String)
    job_id = Column(UUID(as_uuid=True), nullable=True)
    transaction_date = Column(DateTime, default=datetime.utcnow)
