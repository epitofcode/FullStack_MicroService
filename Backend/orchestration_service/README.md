# Orchestration Service

**Role:** The Engine Room & AI Worker

This is a headless background service that does the heavy lifting. It listens for jobs from the queue and communicates with external AI provider APIs.

## Features

*   **Message Queue Consumer:** Continuously listens to the RabbitMQ `ml_jobs` queue for new tasks.
*   **Dynamic Provider Dispatching:** Reads the `model_identifier` from a job and calls the corresponding function to handle the API request (e.g., calls OpenAI, Sarvam.ai, etc.).
*   **Resilient and Reliable:** Built with error handling and automatic reconnection logic to ensure no jobs are lost if RabbitMQ or the database is temporarily unavailable.
*   **Real-time Status Updates:** Updates the job status in the `queue_db` from `PROCESSING` to `COMPLETED` or `FAILED`.
*   **Secure Credential Management:** Loads all third-party API keys securely from a `.env` file.

## Setup & Launch

1.  **Navigate to this directory** in a dedicated terminal.
2.  **Create and activate a virtual environment** and **install dependencies** as described in the main README.
3.  **Create `.env` file:**
    Create a file named `.env` in this directory and add your AI provider API keys:
    ```env
    OPENAI_API_KEY=sk-...
    SARVAM_API_KEY=sk-...
    GOOGLE_API_KEY=...
    AZURE_API_KEY=...
    AZURE_SPEECH_REGION=...
    ```
4.  **Set Environment Variables:**
    ```powershell
    $env:DATABASE_URL_QUEUE = "postgresql://farmvidhya:password@localhost:5432/queue_db"
    $env:RABBITMQ_HOST = "localhost"
    ```
5.  **Launch the Worker:**
    ```powershell
    python worker.py
    ```
This service has no API. Monitor its log output in the terminal to see it process jobs in real time.
