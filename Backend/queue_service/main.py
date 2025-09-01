import os
import requests
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from uuid import UUID
import crud, models, schemas, messaging
from database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")

app = FastAPI(
    title="FarmVidhya Queue Service",
    description="Accepts ML jobs, puts them in a queue, and tracks their status.",
    version="1.0.0"
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="http://127.0.0.1:8001/login")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_current_user_id(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("user_id")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    return UUID(user_id)


@app.post("/jobs", response_model=schemas.JobOut, status_code=status.HTTP_202_ACCEPTED)
def submit_job(
    job: schemas.JobCreate,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id)
):
    JOB_COST = 10
    BILLING_SERVICE_URL = "http://127.0.0.1:8002"

    try:
        # Step 1: Check the user's balance by calling the billing service
        balance_response = requests.get(f"{BILLING_SERVICE_URL}/balance/{current_user_id}")
        balance_response.raise_for_status()
        current_balance = balance_response.json().get("balance")

        # Step 2: If balance is insufficient, reject the job
        if current_balance < JOB_COST:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail="Please Pay and recharge your Credits to continue"
            )

        # Step 3: Tell the billing service to deduct credits
        deduct_payload = {"user_id": str(current_user_id), "amount": JOB_COST}
        deduct_response = requests.post(f"{BILLING_SERVICE_URL}/transactions/deduct", json=deduct_payload)
        deduct_response.raise_for_status()

    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Could not connect to the Billing Service: {e}"
        )

    # If all checks and deductions pass, proceed to create and queue the job
    db_job = crud.create_job(db=db, job=job, user_id=current_user_id)
    
    job_details = {
        "job_id": str(db_job.id),
        "user_id": str(db_job.user_id),
        "model_identifier": db_job.model_identifier,
        "input_url": str(db_job.input_url)
    }
    
    if not messaging.publish_job(job_details):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to queue job after credit deduction. Please contact support."
        )
        
    return db_job

@app.get("/jobs", response_model=list[schemas.JobOut])
def get_jobs_for_user(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id)
):
    return crud.get_user_jobs(db=db, user_id=current_user_id, skip=skip, limit=limit)

@app.get("/jobs/{job_id}", response_model=schemas.JobOut)
def get_job_status(
    job_id: UUID,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id)
):
    db_job = crud.get_job(db=db, job_id=job_id, user_id=current_user_id)
    if db_job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return db_job
