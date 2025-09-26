import os
import json
import structlog
from kafka import KafkaProducer
from kafka.errors import KafkaError

log = structlog.get_logger()
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
EMAIL_TOPIC = "email_topic"

try:
    producer = KafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS, value_serializer=lambda v: json.dumps(v).encode('utf-8'), retries=3, acks='all')
    log.info("✅ Identity Service: Kafka producer connected.")
except KafkaError as e:
    log.error("❌ Identity Service: Kafka producer connection failed.", error=str(e))
    producer = None

def publish_email_task(email: str, otp: str) -> bool:
    if not producer:
        log.error("Cannot publish email task, producer is not available.")
        return False
    message = {"email_type": "otp_verification", "recipient": email, "payload": {"otp": otp}}
    try:
        future = producer.send(EMAIL_TOPIC, value=message)
        future.get(timeout=10)
        log.info("🚀 OTP email task published to Kafka.", recipient=email)
        return True
    except KafkaError as e:
        log.error("Failed to publish email task to Kafka.", error=str(e))
        return False