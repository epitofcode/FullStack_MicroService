from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from .database import Base
from datetime import datetime, timezone
import uuid
import enum

class UserBalance(Base):
    __tablename__ = "user_balances"
    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    balance = Column(Integer, nullable=False, default=10000)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class CreditPolicy(Base):
    __tablename__ = "credit_policies"
    model_identifier = Column(String, primary_key=True)
    price_in_paise = Column(Integer, nullable=False)

class TransactionType(str, enum.Enum):
    CREDIT = "credit"
    DEBIT = "debit"

class TransactionsTillDate(Base):
    __tablename__ = "transactions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("user_balances.user_id"), nullable=False, index=True)
    amount = Column(Integer, nullable=True)
    credits = Column(Integer, nullable=False)
    description = Column(String, nullable=True)
    transaction_type = Column(Enum(TransactionType), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))