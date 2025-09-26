import os
import json
import structlog
from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaError

log = structlog.get_logger()
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
JOBS_TOPIC = "jobs_topic"
DLQ_TOPIC = "dlq_topic"
producer: AIOKafkaProducer | None = None

async def get_kafka_producer():
    global producer
    if producer is None:
        producer = AIOKafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS, value_serializer=lambda v: json.dumps(v).encode('utf-8'))
        await producer.start()
    return producer

async def stop_kafka_producer():
    if producer: await producer.stop()

async def publish_job_for_retry(job_details: dict):
    kafka_producer = await get_kafka_producer()
    try:
        await kafka_producer.send_and_wait(JOBS_TOPIC, value=job_details)
        log.warning("Job re-published for retry.", job_id=job_details.get('job_id'))
    except KafkaError as e:
        log.error("Failed to re-publish job for retry.", error=str(e))

async def publish_to_dlq(job_details: dict, reason: str):
    kafka_producer = await get_kafka_producer()
    try:
        job_details['failure_reason'] = reason
        await kafka_producer.send_and_wait(DLQ_TOPIC, value=job_details)
        log.error("Job sent to Dead-Letter Queue.", job_id=job_details.get('job_id'))
    except KafkaError as e:
        log.error("Failed to publish to DLQ.", error=str(e))
