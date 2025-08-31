from sqlalchemy.orm import Session
import models, schemas # <-- FIX IS HERE
from uuid import UUID

def create_job(db: Session, job: schemas.JobCreate, user_id: UUID):
    db_job = models.Job(**job.model_dump(), user_id=user_id)
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    return db_job

def get_job(db: Session, job_id: UUID, user_id: UUID):
    return db.query(models.Job).filter(models.Job.id == job_id, models.Job.user_id == user_id).first()

def get_user_jobs(db: Session, user_id: UUID, skip: int = 0, limit: int = 100):
    return db.query(models.Job).filter(models.Job.user_id == user_id).order_by(models.Job.created_at.desc()).offset(skip).limit(limit).all()