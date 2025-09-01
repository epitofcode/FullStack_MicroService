from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from contextlib import asynccontextmanager
from typing import List

import crud, models, schemas
from database import SessionLocal, engine 

@asynccontextmanager
async def lifespan(app: FastAPI):
    # This code runs once when the application starts up
    print("Billing Service starting up...")
    db = SessionLocal()
    try:
        crud.create_initial_policies(db)
        print("Initial credit policies seeded successfully.")
    finally:
        db.close()
    yield
    # This code runs once when the application shuts down
    print("Billing Service shutting down...")

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="FarmVidhya Billing Service",
    description="Handles user credit balances and model usage policies.",
    version="1.0.0",
    lifespan=lifespan
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/transactions/deduct", response_model=schemas.UserBalanceOut)
def process_deduction(request: schemas.DeductRequest, db: Session = Depends(get_db)):
    updated_balance = crud.deduct_credits(db, user_id=request.user_id, amount=request.amount)
    if updated_balance is None:
        raise HTTPException(
            status_code=402, # Payment Required
            detail="Insufficient credits."
        )
    return updated_balance

@app.get("/balance/{user_id}", response_model=schemas.UserBalanceOut)
def read_user_balance(user_id: UUID, db: Session = Depends(get_db)):
    balance = crud.get_user_balance(db, user_id=user_id)
    if balance is None:
        raise HTTPException(status_code=404, detail="User not found")
    return balance

@app.get("/policies", response_model=list[schemas.CreditPolicyOut])
def read_policies(db: Session = Depends(get_db)):
    return crud.get_all_policies(db=db)

@app.get("/policies/rules", response_model=List[str])
def get_credit_rules():
    """Returns the rules and regulations for credit usage."""
    return [
        "A new account is credited with 100 free credits upon creation.",
        "Each submitted job costs 10 credits.",
        "Credit deduction occurs before a job is processed.",
        "If your balance is below the job cost, the job will be rejected.",
        "Credits are non-refundable and non-transferable.",
        "This is a Proof of Concept: the credit system is for demonstration purposes only."
    ]
