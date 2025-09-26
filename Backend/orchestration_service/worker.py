from dotenv import load_dotenv
import os
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path=dotenv_path)

import json
import structlog
import asyncio
import httpx
import tempfile
from uuid import UUID
from aiokafka import AIOKafkaConsumer

from . import kafka_utils, db_utils, azure_utils
from .database import AsyncSessionLocal
from sqlalchemy import update
from .models import Job

# --- Configuration ---
log = structlog.get_logger()
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
KAFKA_JOBS_TOPIC = "jobs_topic"
KAFKA_GROUP_ID = "orchestration_group"
MAX_RETRIES = 3
BILLING_SERVICE_URL = os.getenv("BILLING_SERVICE_URL")

# --- ML Service URLs from .env ---
STT_API_URL = os.getenv("STT_API_URL")
NMT_API_URL = os.getenv("NMT_API_URL")
LI_RAG_API_URL = os.getenv("LI_RAG_API_URL")
TTS_API_URL = os.getenv("TTS_API_URL")

# --- Polling Configuration ---
POLLING_INTERVAL_SECONDS = 5
POLLING_TIMEOUT_SECONDS = 300 # 5 minutes

# --- HELPER FUNCTIONS ---

async def update_db(job_id: UUID, status: str, result_data: dict = None, error_message: str = None):
    """A robust helper to update the job status in the database."""
    async with AsyncSessionLocal() as session:
        async with session.begin():
            stmt = update(Job).where(Job.id == job_id).values(
                status=status, 
                result_data=result_data, 
                error_message=error_message
            )
            await session.execute(stmt)
    log.info("Database updated for job.", job_id=str(job_id), status=status)


async def poll_for_completion(client: httpx.AsyncClient, status_url: str, job_id: str) -> dict:
    """A generic, reusable polling function for asynchronous services like STT and TTS."""
    log.info("Starting polling loop.", job_id=job_id, url=status_url)
    start_time = asyncio.get_event_loop().time() # Use a monotonic clock for timeouts

    while True:
        # --- DEFINITIVE FIX: Check for timeout at the start of each loop ---
        elapsed_time = asyncio.get_event_loop().time() - start_time
        if elapsed_time >= POLLING_TIMEOUT_SECONDS:
            raise Exception(f"Polling timed out after {POLLING_TIMEOUT_SECONDS} seconds.")

        try:
            response = await client.get(status_url)
            
            if response.status_code == 404:
                raise Exception(f"Job ID not found at polling endpoint (HTTP 404).")
            
            response.raise_for_status()
            data = response.json()
            
            if data.get("status") in ["completed", "successful"]:
                log.info("Polling successful, job completed.", job_id=job_id, response=data)
                return data
            elif data.get("status") == "failed":
                raise Exception(f"Job failed at external service. Reason: {data.get('result')}")
            
            log.info("Job still processing...", job_id=job_id, status=data.get("status"))

        except httpx.HTTPError as e:
            log.error("HTTP error during polling, will retry.", job_id=job_id, error=str(e))
        
        # Wait before the next poll
        await asyncio.sleep(POLLING_INTERVAL_SECONDS)
# --- ML API CALLER FUNCTIONS (Based on our successful curl tests) ---

async def call_stt_service(client: httpx.AsyncClient, file_path: str) -> str:
    """Calls the asynchronous STT service and returns the transcribed text."""
    log.info("Workflow Step: Calling STT service...")
    with open(file_path, 'rb') as f:
        files = {'file': (os.path.basename(file_path), f, 'audio/wav')}
        data = {'service_id': '3', 'lang_id': 'te-IN'}
        
        response = await client.post(STT_API_URL, files=files, data=data)
        response.raise_for_status()
        
    initial_data = response.json()
    stt_job_id = initial_data.get("job_id")
    if not stt_job_id: raise Exception("STT service did not return a job_id.")

    status_url = f"https://api.farmvaidya.ai/v1/status/{stt_job_id}"
    completed_data = await poll_for_completion(client, status_url, stt_job_id)
    return completed_data.get("result")

async def call_nmt_service(client: httpx.AsyncClient, text_to_translate: str, target_lang: str) -> str:
    """A reusable, synchronous NMT function."""
    log.info("Workflow Step: Calling NMT service...", target_language=target_lang)
    payload = {"text": text_to_translate, "target_language": target_lang}
    response = await client.post(NMT_API_URL, json=payload)
    response.raise_for_status()
    return response.json().get("translation")

async def call_rag_service(client: httpx.AsyncClient, english_question: str) -> str:
    """Calls the synchronous RAG service using query params and returns the answer."""
    log.info("Workflow Step: Calling RAG service...")
    
    sanitized_question = english_question.strip().strip('"')
    params = {"question": sanitized_question}
    
    response = await client.post(LI_RAG_API_URL, params=params)
    response.raise_for_status()
    
    data = response.json()
    if data.get("type") == "follow_up_required":
        return data.get("follow_up_question")
    else:
        return data.get("response")

async def call_tts_service(client: httpx.AsyncClient, text_for_speech: str) -> bytes:
    """Calls the asynchronous TTS service with Telugu text and returns the binary audio."""
    log.info("Workflow Step: Calling TTS service...")
    payload = {
        "text": text_for_speech,
        "lang_id": "tel",
        "service_id": "12345678"
    }
    response = await client.post(TTS_API_URL, json=payload)
    response.raise_for_status()

    initial_data = response.json()
    tts_job_id = initial_data.get("job_id")
    if not tts_job_id: raise Exception("TTS service did not return a job_id.")
    
    status_url = f"https://api.farmvaidya.ai/v4/tts/status/{tts_job_id}"
    await poll_for_completion(client, status_url, tts_job_id)
    
    log.info("TTS job complete, downloading audio...", job_id=tts_job_id)
    download_url = f"https://api.farmvaidya.ai/v4/tts/download/{tts_job_id}"
    download_response = await client.get(download_url)
    download_response.raise_for_status()
    return download_response.content

# --- MAIN WORKFLOW ORCHESTRATOR ---

async def process_job(job_info: dict, client: httpx.AsyncClient):
    job_id = UUID(str(job_info.get('job_id')))
    log.info("▶️ Processing job", job_id=str(job_id))
    
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            job = await db_utils.get_job_details(job_id)
            if not job: raise ValueError("Job details not found in database.")
            
            source_blob_name = job.blob_name
            local_source_path = os.path.join(temp_dir, os.path.basename(source_blob_name))
            if not await azure_utils.download_blob_to_path(source_blob_name, local_source_path):
                raise Exception("Failed to download source file from Azure.")
            
            # Step 1: STT (Telugu Audio -> Telugu Text)
            stt_telugu_text = await call_stt_service(client, local_source_path)
            if not stt_telugu_text: raise Exception("STT returned empty text.")
            
            # Step 2: NMT (Telugu Text -> English Text)
            nmt_english_text = await call_nmt_service(client, text_to_translate=stt_telugu_text, target_lang="english")
            if not nmt_english_text: raise Exception("NMT to English returned empty text.")

            # Step 3: RAG (English Text -> English Answer)
            rag_english_answer = await call_rag_service(client, nmt_english_text)
            if not rag_english_answer: raise Exception("RAG returned empty text.")
            
            # Step 4: NMT (English Answer -> Telugu Answer)
            final_telugu_answer = await call_nmt_service(client, text_to_translate=rag_english_answer, target_lang="telugu")
            if not final_telugu_answer: raise Exception("NMT to Telugu returned empty text.")

            # Step 5: TTS (Telugu Answer -> Telugu Audio)
            final_audio_bytes = await call_tts_service(client, final_telugu_answer)
            if not final_audio_bytes: raise Exception("TTS returned empty audio.")
            
            # Finalization
            local_result_path = os.path.join(temp_dir, "output.mp3")
            with open(local_result_path, 'wb') as f:
                f.write(final_audio_bytes)
            
            result_blob_name = f"{job_id}/output.mp3"
            result_url = await azure_utils.upload_file_to_blob(local_result_path, result_blob_name)
            if not result_url: raise Exception("Failed to upload result file.")
            
            final_result = {"result_audio_url": result_url}

            if BILLING_SERVICE_URL:
                billing_payload = {"user_id": str(job.user_id), "model_identifier": "stt-sarvam-v1"}
                await client.post(f"{BILLING_SERVICE_URL}/credits/deduct", json=billing_payload)
                log.info("Credits deducted successfully.", job_id=str(job_id))

            await update_db(job_id, "COMPLETED", result_data=final_result)
            log.info("✅ Job/Workflow completed successfully.", job_id=str(job_id))

        except Exception as e:
            error_msg = str(e)
            log.error("❌ Job failed.", job_id=str(job_id), error=error_msg)
            
            job_info['retry_count'] = job_info.get('retry_count', 0) + 1
            if job_info['retry_count'] < MAX_RETRIES:
                log.warning("Publishing job for retry.", job_id=str(job_id), retry_count=job_info['retry_count'])
                await kafka_utils.publish_job_for_retry(job_info)
            else:
                log.critical("Job failed max retries. Sending to DLQ.", job_id=str(job_id))
                await update_db(job_id, "FAILED", error_message=error_msg)
                await kafka_utils.publish_to_dlq(job_info, reason=error_msg)

# --- KAFKA CONSUMER ENTRY POINT ---

async def main():
    log.info("Orchestration Worker starting...")
    consumer = AIOKafkaConsumer(
        KAFKA_JOBS_TOPIC, 
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS, 
        group_id=KAFKA_GROUP_ID,
        auto_offset_reset='earliest',
        value_deserializer=lambda x: json.loads(x.decode('utf-8')),
        enable_auto_commit=False
    )
    
    await consumer.start()
    log.info("✅ Orchestration worker connected to Kafka.")
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            async for message in consumer:
                await process_job(message.value, client)
                await consumer.commit()
        finally:
            log.warning("Shutting down worker...")
            await consumer.stop()
            await kafka_utils.stop_kafka_producer()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log.info("Shutdown requested by user.")
