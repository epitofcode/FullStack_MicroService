# Queue Service

## Description

This service is the **Job Dispatcher**. It serves as the main, authenticated entry point for all long-running AI tasks. Its primary responsibility is to validate a user's request, create a persistent job record for tracking, and then hand off the actual work to the background processing system via a message queue. This asynchronous pattern ensures the user receives an immediate response and the API remains fast and responsive.

## Tech Stack & Core Dependencies

*   **Framework:** FastAPI
*   **Database:** PostgreSQL with SQLAlchemy (ORM)
*   **Message Broker Client:** `pika` for communicating with RabbitMQ.
*   **Security:** `python-jose[cryptography]` for decoding and validating JWTs received from users.

## Core Concepts & Flow

The service follows a decoupled, asynchronous workflow.

1.  **Authentication:** An incoming request to `POST /jobs` must include a valid JWT in the `Authorization` header. A FastAPI dependency automatically decodes this token to securely identify the user and extract their `user_id`.
2.  **Job Creation:** Upon successful authentication, a new record is immediately created in the `jobs` table of the `queue_db`. This job is given a unique `job_id` and is marked with an initial status of `PENDING`.
3.  **Message Queuing:** A small message containing the `job_id` and other essential details is published to the `ml_jobs` queue in RabbitMQ. This message is marked as "persistent" to ensure it survives a RabbitMQ restart.
4.  **Immediate Response:** As soon as the message is successfully published, the service sends a `202 Accepted` response back to the user, which includes the `job_id`. The user can now use this ID to check the status of their job later.

## API Endpoints

*   `POST /jobs`: Submit a new AI job for processing. Requires authentication.
*   `GET /jobs`: Get a list of all jobs submitted by the authenticated user.
*   `GET /jobs/{job_id}`: Get the current status and details of a specific job.
*   `GET /docs`: Interactive API documentation.

## How to Run Locally

1.  **Navigate to Directory:** `cd Backend/queue_service`
2.  **Create & Activate Venv:**
    ```bash
    python -m venv venv
    .\venv\Scripts\Activate.ps1
    ```
3.  **Install Dependencies:** `pip install -r requirements.txt`
4.  **Set Environment Variables (PowerShell):**
    ```powershell
    $env:DATABASE_URL = "postgresql://farmvidhya:password@localhost:5432/queue_db"
    $env:RABBITMQ_HOST = "localhost"
    $env:SECRET_KEY = "a_very_secret_key_for_jwt_tokens"
    $env:ALGORITHM = "HS256"
    ```
5.  **Run Server:** `uvicorn main:app --reload --port 8003`
