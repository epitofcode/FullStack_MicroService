import os
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from uuid import UUID
import crud, models, schemas, messaging # <-- FIX IS HERE
from database import SessionLocal, engine # <-- FIX IS HERE

models.Base.metadata.create_all(bind=engine)

# These must match the user_service to decode tokens correctly
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
            detail="Failed to queue job. Please try again later."
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