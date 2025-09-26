from dotenv import load_dotenv
import os
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path=dotenv_path)

import razorpay
from fastapi import FastAPI, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
import structlog

from . import crud, models, schemas
from .database import AsyncSessionLocal, engine, Base

RAZORPAY_API_KEY = os.getenv("RAZORPAY_API_KEY")
RAZORPAY_API_SECRET = os.getenv("RAZORPAY_API_SECRET")
RAZORPAY_WEBHOOK_SECRET = os.getenv("RAZORPAY_WEBHOOK_SECRET")
log = structlog.get_logger()
app = FastAPI(title="FarmVidhya Billing Service", description="Manages user credits, pricing, and payment integration.", version="2.0.0")
client = razorpay.Client(auth=(RAZORPAY_API_KEY, RAZORPAY_API_SECRET)) if RAZORPAY_API_KEY else None

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncSessionLocal() as session:
        await crud.create_initial_policies(session)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

@app.get("/balance/{user_id}", response_model=schemas.UserBalanceOut, tags=["Billing"])
async def read_user_balance(user_id: UUID, db: AsyncSession = Depends(get_db)):
    return await crud.get_or_create_user_balance(db, user_id=user_id)

@app.post("/initiate-payment", tags=["Billing"])
async def initiate_payment(payment_data: schemas.PaymentRequest):
    if not client: raise HTTPException(status_code=501, detail="Razorpay is not configured.")
    try:
        payment_link_data = {"amount": int(payment_data.amount * 100), "currency": "INR", "description": "Credits for FarmVidhya.ai", "customer": {"name": payment_data.name, "email": payment_data.email, "contact": payment_data.phone}, "notify": {"sms": True, "email": True}, "callback_url": "https://your-frontend-url.com/payment-success", "callback_method": "get", "notes": {"internal_user_id": str(payment_data.user_id)}}
        payment_link = client.payment_link.create(payment_link_data)
        return {"payment_url": payment_link.get("short_url")}
    except Exception as e:
        log.error("Razorpay payment link creation failed.", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/webhook/razorpay", tags=["Webhooks"])
async def handle_razorpay_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    if not client: raise HTTPException(status_code=501, detail="Razorpay is not configured.")
    body = await request.body()
    try:
        client.utility.verify_webhook_signature(body.decode('utf-8'), request.headers.get('x-razorpay-signature'), RAZORPAY_WEBHOOK_SECRET)
    except razorpay.errors.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid Razorpay signature")
    data = await request.json()
    log.info("Razorpay webhook received.", event=data.get("event"))
    if data.get("event") == "payment_link.paid":
        payment_entity = data['payload']['payment_link']['entity']
        notes = payment_entity.get("notes", {})
        user_id_str = notes.get("internal_user_id")
        amount_inr = int(payment_entity.get("amount", 0)) / 100
        if not user_id_str or amount_inr <= 0:
            log.error("Webhook missing user_id or amount.", payload=payment_entity)
            return {"status": "error", "message": "Payload missing required fields"}
        await crud.add_credits_from_payment(db=db, user_id=UUID(user_id_str), amount_inr=int(amount_inr))
        log.info("Credits added successfully from webhook.", user_id=user_id_str, amount=amount_inr)
        return {"status": "ok"}
    return {"status": "ignored"}

@app.post("/credits/check-balance", status_code=status.HTTP_204_NO_CONTENT, include_in_schema=False)
async def check_balance(request: schemas.CreditActionRequest, db: AsyncSession = Depends(get_db)):
    policy = await crud.get_credit_policy(db, request.model_identifier)
    if not policy: raise HTTPException(status_code=400, detail=f"No pricing policy found for model: {request.model_identifier}")
    user_balance = await crud.get_or_create_user_balance(db, user_id=request.user_id)
    if user_balance.balance < policy.price_in_paise: raise HTTPException(status_code=402, detail="Insufficient credits")
    return

@app.post("/credits/deduct", status_code=status.HTTP_204_NO_CONTENT, include_in_schema=False)
async def deduct_credits_for_job(request: schemas.CreditActionRequest, db: AsyncSession = Depends(get_db)):
    policy = await crud.get_credit_policy(db, request.model_identifier)
    if not policy: raise HTTPException(status_code=400, detail=f"No pricing policy found for model: {request.model_identifier}")
    success = await crud.deduct_credits(db, user_id=request.user_id, amount=policy.price_in_paise)
    if not success: raise HTTPException(status_code=402, detail="Deduction failed; insufficient credits")
    return