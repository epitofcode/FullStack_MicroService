import pika
import os
import json
import logging

logging.basicConfig(level=logging.INFO)

def get_rabbitmq_connection():
    """Establishes a connection to RabbitMQ."""
    rabbitmq_host = os.getenv("RABBITMQ_HOST", "localhost")
    try:
        return pika.BlockingConnection(pika.ConnectionParameters(host=rabbitmq_host))
    except pika.exceptions.AMQPConnectionError:
        logging.error("Could not connect to RabbitMQ. Please ensure it is running.")
        return None

def publish_job(job_details: dict):
    """Publishes a job to the ml_jobs queue."""
    connection = get_rabbitmq_connection()
    if not connection:
        return False
    
    try:
        channel = connection.channel()
        # Declare a durable queue to ensure messages are not lost if RabbitMQ restarts
        channel.queue_declare(queue='ml_jobs', durable=True)
        
        message_body = json.dumps(job_details)
        
        channel.basic_publish(
            exchange='',
            routing_key='ml_jobs',
            body=message_body,
            properties=pika.BasicProperties(
                delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE,  # Make message persistent
            ))
        logging.info(f" [x] Sent job {job_details.get('job_id')} to the queue.")
        return True
    except Exception as e:
        logging.error(f"Failed to publish job to RabbitMQ: {e}")
        return False
    finally:
        if connection.is_open:
            connection.close()