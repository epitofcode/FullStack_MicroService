from dotenv import load_dotenv
import os
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path=dotenv_path)

from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from uuid import UUID
from typing import List
from fastapi_sso.sso.google import GoogleSSO

from . import kafka_utils, crud, models, schemas, auth
from .database import AsyncSessionLocal, engine, Base

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")
sso = GoogleSSO(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REDIRECT_URI) if GOOGLE_CLIENT_ID else None
app = FastAPI(title="FarmVidhya Identity Service", description="Handles user authentication, authorization, and API key management.", version="1.0.0")

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

@app.post("/signup", status_code=status.HTTP_201_CREATED, tags=["User Authentication"])
async def signup(user: schemas.UserCreate, db: AsyncSession = Depends(get_db)):
    try:
        _, plain_otp = await crud.create_user_with_otp(db=db, user=user)
        if not kafka_utils.publish_email_task(email=user.email, otp=plain_otp):
            raise HTTPException(status_code=503, detail="Failed to queue OTP email.")
        return {"message": "User registered. Please check your email for an OTP."}
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Email already registered.")

@app.post("/verify-otp", status_code=status.HTTP_200_OK, tags=["User Authentication"])
async def verify_otp(request: schemas.OTPSchema, db: AsyncSession = Depends(get_db)):
    user = await crud.get_user_by_email(db, email=request.email)
    if not user or user.provider != 'email': raise HTTPException(status_code=404, detail="User not found or not registered with email.")
    if user.is_active: raise HTTPException(status_code=400, detail="Account already verified.")
    if not await crud.verify_user_otp(db, user=user, otp=request.otp): raise HTTPException(status_code=400, detail="Invalid or expired OTP.")
    return {"message": "Account verified. You can now log in."}

@app.post("/login", response_model=schemas.Token, tags=["User Authentication"])
async def login(db: AsyncSession = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    user = await crud.get_user_by_email(db, email=form_data.username)
    if not user or user.provider != 'email' or not user.hashed_password: raise HTTPException(status_code=401, detail="Incorrect email or password")
    if not user.is_active: raise HTTPException(status_code=403, detail="Account not verified.")
    if not auth.verify_password(form_data.password, user.hashed_password): raise HTTPException(status_code=401, detail="Incorrect email or password")
    access_token = auth.create_access_token(data={"sub": str(user.id), "email": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/auth/google/login", tags=["User Authentication"])
async def google_login():
    if not sso: raise HTTPException(status_code=501, detail="Google SSO is not configured.")
    return await sso.get_login_redirect()

@app.get("/auth/google/callback", response_model=schemas.Token, tags=["User Authentication"])
async def google_callback(request: Request, db: AsyncSession = Depends(get_db)):
    if not sso: raise HTTPException(status_code=501, detail="Google SSO is not configured.")
    user_info = await sso.verify_and_process(request)
    if not user_info: raise HTTPException(status_code=401, detail="Google authentication failed.")
    user = await crud.get_or_create_google_user(db, user_info=user_info.dict())
    access_token = auth.create_access_token(data={"sub": str(user.id), "email": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/keys", response_model=schemas.APIKeyCreateOut, status_code=201, tags=["API Key Management"])
async def issue_new_key(request: schemas.APIKeyCreateRequest, db: AsyncSession = Depends(get_db)):
    db_key, plain_key = await crud.create_api_key(db, user_id=request.user_id)
    return schemas.APIKeyCreateOut(id=db_key.id, plain_key=plain_key, key_prefix=db_key.key_prefix, user_id=db_key.user_id, created_at=db_key.created_at)

@app.get("/keys/user/{user_id}", response_model=List[schemas.APIKeyInfoOut], tags=["API Key Management"])
async def get_keys_for_user(user_id: UUID, db: AsyncSession = Depends(get_db)):
    return await crud.get_user_api_keys(db, user_id=user_id)

@app.delete("/keys/{key_id}/user/{user_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["API Key Management"])
async def deactivate_key(key_id: UUID, user_id: UUID, db: AsyncSession = Depends(get_db)):
    success = await crud.revoke_api_key(db, key_id=key_id, user_id=user_id)
    if not success: raise HTTPException(status_code=404, detail="API Key not found or does not belong to user")
    return

@app.post("/keys/validate", response_model=schemas.APIKeyValidateOut, include_in_schema=False, tags=["Internal"])
async def validate_api_key(request: schemas.APIKeyValidateRequest, db: AsyncSession = Depends(get_db)):
    plain_key = request.plain_key
    if not plain_key or not plain_key.startswith("fv_"): raise HTTPException(status_code=400, detail="Invalid key format")
    KEY_PREFIX_LENGTH = 12
    key_prefix = plain_key[:KEY_PREFIX_LENGTH]
    db_key = await crud.get_key_by_prefix(db, key_prefix=key_prefix)
    if not db_key: raise HTTPException(status_code=401, detail="Invalid API Key")
    if not auth.verify_api_key(plain_key, db_key.key_hash): raise HTTPException(status_code=401, detail="Invalid API Key")
    if not db_key.is_active: raise HTTPException(status_code=403, detail="API Key is inactive")
    return schemas.APIKeyValidateOut(user_id=db_key.user_id, is_active=db_key.is_active)