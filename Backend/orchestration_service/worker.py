import pika
import os
import time
import json
import logging
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime
from database import SessionLocal, Base, engine

# Set up basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# This worker needs a representation of the Job model to update it.
# It must exactly match the model in the queue_service.
from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

class Job(Base):
    __tablename__ = 'jobs'
    id = Column(PG_UUID(as_uuid=True), primary_key=True)
    status = Column(String)
    output_url = Column(String)
    error_message = Column(String)
    completed_at = Column(DateTime)
    __table_args__ = {'extend_existing': True}


def process_job(job_details: dict):
    """
    THIS IS THE CORE ML PROCESSING LOGIC (CURRENTLY A SIMULATION).
    In the real world, this function would:
    1. Download the file from job_details['input_url'].
    2. Load the appropriate ML model (e.g., Telugu SST).
    3. Run the inference.
    4. Save the results (e.g., a text file).
    5. Upload the result file to a storage service (like AWS S3).
    6. Return the public URL of the result file.
    """
    job_id = job_details.get('job_id')
    model = job_details.get('model_identifier')
    logging.info(f"[->] Received job {job_id} for model '{model}'. Simulating ML work...")
    
    # Simulate a long-running ML task
    time.sleep(15) 
    
    # Simulate a successful result
    output_url = f"https://farmvidhya.ai/results/{job_id}.txt"
    logging.info(f"[✓] Finished processing job {job_id}. Mock output at: {output_url}")
    return "COMPLETED", output_url, None

def update_job_status(job_id: UUID, status: str, output_url: str = None, error: str = None):
    """Updates the job status in the database."""
    db: Session = SessionLocal()
    try:
        job_to_update = db.query(Job).filter(Job.id == job_id).first()
        if job_to_update:
            job_to_update.status = status
            job_to_update.output_url = output_url
            job_to_update.error_message = error
            job_to_update.completed_at = datetime.utcnow()
            db.commit()
            logging.info(f"Updated status for job {job_id} to {status}.")
        else:
            logging.warning(f"Could not find job {job_id} in DB to update status.")
    except Exception as e:
        logging.error(f"DB Error while updating job {job_id}: {e}")
        db.rollback()
    finally:
        db.close()

def main():
    rabbitmq_host = os.getenv("RABBITMQ_HOST", "localhost")
    logging.info("Worker starting. Connecting to RabbitMQ...")
    
    while True:
        try:
            connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitmq_host))
            channel = connection.channel()
            channel.queue_declare(queue='ml_jobs', durable=True)
            logging.info(' [*] Waiting for messages. To exit press CTRL+C')

            def callback(ch, method, properties, body):
                try:
                    job_details = json.loads(body)
                    job_id = UUID(job_details['job_id'])
                except (json.JSONDecodeError, KeyError) as e:
                    logging.error(f"Received malformed message: {body}. Error: {e}")
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False) # Discard bad message
                    return

                # 1. Immediately update status to PROCESSING
                update_job_status(job_id, status="PROCESSING")
                
                # 2. Run the (mock) ML inference
                try:
                    final_status, output_url, error_msg = process_job(job_details)
                except Exception as e:
                    logging.error(f"An unexpected error occurred during ML processing for job {job_id}: {e}")
                    final_status = "FAILED"
                    output_url = None
                    error_msg = "An internal error occurred during processing."

                # 3. Update status to COMPLETED or FAILED
                update_job_status(job_id, status=final_status, output_url=output_url, error=error_msg)
                
                # 4. Acknowledge the message was successfully processed
                ch.basic_ack(delivery_tag=method.delivery_tag)

            channel.basic_qos(prefetch_count=1) # Process one message at a time
            channel.basic_consume(queue='ml_jobs', on_message_callback=callback)
            channel.start_consuming()

        except pika.exceptions.AMQPConnectionError:
            logging.warning("Connection to RabbitMQ failed. Retrying in 5 seconds...")
            time.sleep(5)
        except Exception as e:
            logging.error(f"An unhandled error occurred in the main loop: {e}")
            time.sleep(5)


if __name__ == '__main__':
    main()