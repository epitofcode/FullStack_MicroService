from dotenv import load_dotenv
import os
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path=dotenv_path)

from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID, uuid4
import requests
import structlog

from . import crud, models, schemas
from .database import AsyncSessionLocal, engine, Base
from .azure_utils import generate_sas_upload_url

log = structlog.get_logger()
BILLING_SERVICE_URL = os.getenv("BILLING_SERVICE_URL")
app = FastAPI(title="FarmVidhya Queue Service", description="Handles the staging and queueing of all asynchronous jobs.", version="2.0.0")

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

def check_user_credits(user_id: str, model_identifier: str):
    if not BILLING_SERVICE_URL: raise HTTPException(status_code=500, detail="Billing service is not configured")
    try:
        response = requests.post(f"{BILLING_SERVICE_URL}/credits/check-balance", json={"user_id": user_id, "model_identifier": model_identifier}, timeout=5)
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        detail = e.response.json().get("detail", "Credit check failed")
        raise HTTPException(status_code=e.response.status_code, detail=detail)
    except requests.exceptions.RequestException:
        raise HTTPException(status_code=503, detail="Billing service is unavailable")

@app.post("/jobs/initiate-upload", response_model=schemas.UploadInitiationOut, status_code=201)
async def initiate_file_upload(request: schemas.UploadInitiationIn, user_id: UUID, db: AsyncSession = Depends(get_db)):
    log.info("Upload initiation request received.", user_id=str(user_id), filename=request.filename)
    if not request.model_identifier and not request.workflow_type: raise HTTPException(status_code=422, detail="Either 'model_identifier' or 'workflow_type' must be provided.")
    if request.model_identifier and request.workflow_type: raise HTTPException(status_code=422, detail="Cannot provide both 'model_identifier' and 'workflow_type'.")
    
    credit_check_identifier = request.model_identifier
    if request.workflow_type == "conversational-agent-telugu": credit_check_identifier = "stt-sarvam-v1"
    if not credit_check_identifier: raise HTTPException(status_code=400, detail="Could not determine a model for credit check.")
    check_user_credits(str(user_id), credit_check_identifier)

    job_id = uuid4()
    blob_name = f"{job_id}/{request.filename}"
    db_job = await crud.create_job_for_upload(db, user_id=user_id, job_data=request, blob_name=blob_name, job_id=job_id)

    upload_url = generate_sas_upload_url(blob_name=blob_name)
    if not upload_url:
        log.error("Failed to generate Azure SAS URL.", job_id=str(db_job.id))
        raise HTTPException(status_code=500, detail="Could not generate upload URL.")

    return schemas.UploadInitiationOut(job_id=db_job.id, upload_url=upload_url)