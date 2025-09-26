from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from uuid import UUID
from . import models

async def get_or_create_user_balance(db: AsyncSession, user_id: UUID) -> models.UserBalance:
    result = await db.execute(select(models.UserBalance).filter(models.UserBalance.user_id == user_id))
    db_balance = result.scalars().first()
    if not db_balance:
        try:
            db_balance = models.UserBalance(user_id=user_id)
            db.add(db_balance)
            await db.commit()
            await db.refresh(db_balance)
        except IntegrityError:
            await db.rollback()
            result = await db.execute(select(models.UserBalance).filter(models.UserBalance.user_id == user_id))
            db_balance = result.scalars().one()
    return db_balance

async def get_credit_policy(db: AsyncSession, model_identifier: str) -> models.CreditPolicy | None:
    result = await db.execute(select(models.CreditPolicy).filter(models.CreditPolicy.model_identifier == model_identifier))
    return result.scalars().first()

async def deduct_credits(db: AsyncSession, user_id: UUID, amount: int) -> bool:
    stmt = (update(models.UserBalance).where(models.UserBalance.user_id == user_id).where(models.UserBalance.balance >= amount).values(balance=models.UserBalance.balance - amount))
    result = await db.execute(stmt)
    await db.commit()
    return result.rowcount > 0

async def add_credits_from_payment(db: AsyncSession, user_id: UUID, amount_inr: int) -> models.UserBalance | None:
    CREDIT_MAP = {500: 5000, 1000: 11000, 2000: 23000, 5000: 60000, 10000: 125000}
    credits_to_add = CREDIT_MAP.get(amount_inr)
    if credits_to_add is None: return None
    user_balance = await get_or_create_user_balance(db, user_id)
    user_balance.balance += credits_to_add
    db_transaction = models.TransactionsTillDate(user_id=user_id, amount=amount_inr * 100, credits=credits_to_add, description="Credits added via Razorpay.", transaction_type=models.TransactionType.CREDIT)
    db.add(db_transaction)
    await db.commit()
    await db.refresh(user_balance)
    return user_balance

async def create_initial_policies(db: AsyncSession):
    policies_to_seed = [{"model_identifier": "stt-sarvam-v1", "price_in_paise": 10}, {"model_identifier": "nmt-google-v1", "price_in_paise": 5}, {"model_identifier": "li_rag-custom-v1", "price_in_paise": 20}, {"model_identifier": "tts-elevenlabs-v1", "price_in_paise": 15}]
    for policy_data in policies_to_seed:
        result = await db.execute(select(models.CreditPolicy).filter_by(model_identifier=policy_data["model_identifier"]))
        if not result.scalars().first():
            db.add(models.CreditPolicy(**policy_data))
    await db.commit()