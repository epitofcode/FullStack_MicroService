import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from uuid import UUID
import structlog
from .models import Job

log = structlog.get_logger()
DATABASE_URL = os.getenv("CENTRAL_DATABASE_URL")
engine = create_async_engine(DATABASE_URL)
AsyncSessionLocal = sessionmaker(bind=engine, class_=AsyncSession)

async def get_job_details(job_id: UUID) -> Job | None:
    async with AsyncSessionLocal() as session:
        try:
            result = await session.execute(select(Job).filter(Job.id == job_id))
            job = result.scalars().first()
            if not job: log.warning("Job not found in database.", job_id=str(job_id))
            return job
        except Exception as e:
            log.error("Failed to fetch job details from DB.", error=e, job_id=str(job_id))
            return None