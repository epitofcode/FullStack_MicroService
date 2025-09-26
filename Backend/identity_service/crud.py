from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta, timezone
import random
from uuid import UUID
from . import models, schemas, auth

async def get_user_by_email(db: AsyncSession, email: str):
    result = await db.execute(select(models.User).filter(models.User.email == email))
    return result.scalars().first()

async def create_user_with_otp(db: AsyncSession, user: schemas.UserCreate):
    hashed_password = auth.get_password_hash(user.password)
    plain_otp = str(random.randint(100000, 999999))
    hashed_otp = auth.get_password_hash(plain_otp)
    db_user = models.User(email=user.email, hashed_password=hashed_password, is_active=False, provider='email', otp=hashed_otp, otp_expires_at=datetime.now(timezone.utc) + timedelta(minutes=15))
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user, plain_otp

async def get_or_create_google_user(db: AsyncSession, user_info: dict):
    user = await get_user_by_email(db, email=user_info['email'])
    if not user:
        user = models.User(email=user_info['email'], is_active=True, provider='google')
        db.add(user)
        await db.commit()
        await db.refresh(user)
    return user

async def verify_user_otp(db: AsyncSession, user: models.User, otp: str) -> bool:
    if not user.otp_expires_at or user.otp_expires_at < datetime.now(timezone.utc): return False
    if not auth.verify_password(otp, user.otp): return False
    user.is_active = True
    user.otp = None
    user.otp_expires_at = None
    await db.commit()
    return True

async def create_api_key(db: AsyncSession, user_id: UUID):
    plain_key, hashed_key = auth.generate_api_key()
    KEY_PREFIX_LENGTH = 12
    key_prefix = plain_key[:KEY_PREFIX_LENGTH]
    db_key = models.APIKey(key_hash=hashed_key, user_id=user_id, key_prefix=key_prefix)
    db.add(db_key)
    await db.commit()
    await db.refresh(db_key)
    return db_key, plain_key

async def get_user_api_keys(db: AsyncSession, user_id: UUID):
    result = await db.execute(select(models.APIKey).filter(models.APIKey.user_id == user_id))
    return result.scalars().all()

async def revoke_api_key(db: AsyncSession, key_id: UUID, user_id: UUID):
    result = await db.execute(select(models.APIKey).filter(models.APIKey.id == key_id, models.APIKey.user_id == user_id))
    db_key = result.scalars().first()
    if db_key and db_key.is_active:
        db_key.is_active = False
        await db.commit()
        return True
    return False

async def get_key_by_prefix(db: AsyncSession, key_prefix: str):
    result = await db.execute(select(models.APIKey).filter(models.APIKey.key_prefix == key_prefix))
    return result.scalars().first()