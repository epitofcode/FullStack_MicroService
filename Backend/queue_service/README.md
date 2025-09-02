# Queue Service

**Role:** Job Dispatcher & API Gateway for AI Tasks

This service is the primary entry point for submitting AI jobs. It validates requests and hands them off for background processing.

## Features

*   **Authenticated Job Submission:** Protects the `/jobs` endpoint, ensuring only logged-in users can submit tasks.
*   **Pre-Processing Credit Check:** Communicates with the Billing Service to verify a user's balance and deduct credits *before* queuing a job.
*   **Asynchronous Task Queuing:** Publishes valid job requests to a RabbitMQ message queue.
*   **Instantaneous Response:** Immediately returns a `job_id` to the user, allowing for a non-blocking user experience.
*   **Job Status Tracking:** Provides endpoints to check the status and retrieve the results of a job.

## API Endpoints

*   `POST /jobs`: Submit a new AI job for processing.
*   `GET /jobs`: Get a list of your past and current jobs.
*   `GET /jobs/{job_id}`: Get the detailed status and result of a specific job.

## Setup & Launch

1.  **Navigate to this directory** in a dedicated terminal.
2.  **Create and activate a virtual environment** and **install dependencies** as described in the main README.
3.  **Set Environment Variables:**
    ```powershell
    $env:DATABASE_URL = "postgresql://farmvidhya:password@localhost:5432/queue_db"
    $env:RABBITMQ_HOST = "localhost"
    $env:SECRET_KEY = "a-strong-secret-key-for-your-project" # Must match User Service
    $env:ALGORITHM = "HS256"
    ```
4.  **Launch the Service:**
    ```powershell
    uvicorn main:app --reload --port 8003
    ```
5.  **Access the API Docs:** `http://127.0.0.1:8003/docs`
