from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from . import models, schemas

async def create_job_for_upload(db: AsyncSession, user_id: UUID, job_data: schemas.UploadInitiationIn, blob_name: str, job_id: UUID) -> models.Job:
    db_job = models.Job(
        id=job_id,
        user_id=user_id,
        blob_name=blob_name,
        status='AWAITING_UPLOAD',
        input_data={"original_filename": job_data.filename},
        model_identifier=job_data.model_identifier,
        workflow_type=job_data.workflow_type
    )
    db.add(db_job)
    await db.commit()
    await db.refresh(db_job)
    return db_job