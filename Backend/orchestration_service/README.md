# Orchestration Service (Worker)

## Description

This service is the **Engine Room** of the FarmVidhya platform. It is a headless background worker that has **no API**. Its sole purpose is to listen for new tasks from the RabbitMQ message queue, perform the actual time-consuming AI processing, and update the job status in the database.

## Tech Stack & Core Dependencies

*   **Message Broker Client:** `pika` for consuming messages from RabbitMQ.
*   **Database:** PostgreSQL with SQLAlchemy (ORM) for updating job statuses.

## Core Concepts & Flow

This service is designed for resilience and reliable background processing.

1.  **Connection and Listening:** The `worker.py` script starts an infinite loop. It connects to RabbitMQ and begins listening exclusively to the `ml_jobs` queue. The script includes error handling to automatically reconnect if the connection to RabbitMQ is lost.
2.  **Job Consumption:** When a new message (containing a `job_id`) arrives, the worker's `callback` function is triggered. RabbitMQ marks the message as "Unacknowledged" (`Unacked`), meaning it has been delivered but not yet completed.
3.  **Status Update (Processing):** The worker immediately connects to the `queue_db` and updates the job's status from `PENDING` to `PROCESSING`.
4.  **Work Execution:** The `process_job` function is called. **This is the placeholder where the actual AI model inference code will go.** Currently, it simulates a 15-second task.
5.  **Status Update (Completed):** After the work is finished, the worker connects to the database again and updates the job's status to `COMPLETED`, filling in the result URL.
6.  **Acknowledgement (Ack):** Only after all steps are successfully completed does the worker send an "acknowledgement" (`ack`) signal back to RabbitMQ. This tells RabbitMQ to permanently delete the message from the queue. If the worker crashes at any point before this signal is sent, the message will be safely returned to the queue to be processed again later, ensuring no jobs are ever lost.

## API Endpoints

None. This is a headless background worker and does not expose any HTTP endpoints.

## How to Run Locally

1.  **Navigate to Directory:** `cd Backend/orchestration_service`
2.  **Create & Activate Venv:**
    ```bash
    python -m venv venv
    .\venv\Scripts\Activate.ps1
    ```
3.  **Install Dependencies:** `pip install -r requirements.txt`
4.  **Set Environment Variables (PowerShell):**
    ```powershell
    $env:DATABASE_URL_QUEUE = "postgresql://farmvidhya:password@localhost:5432/queue_db"
    $env:RABBITMQ_HOST = "localhost"
    ```
5.  **Run Worker:** `python worker.py`
