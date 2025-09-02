# FarmVidhya Backend Services (POC1)

Welcome to the backend of the FarmVidhya Conversational AI platform. This repository contains the complete infrastructure for a scalable, multi-provider, and secure AI backend built on a microservices architecture.

This Proof of Concept (POC1) establishes a robust foundation that includes user authentication with OTP verification, a credit-based billing system, an asynchronous job queue for handling long-running tasks, and a dynamic orchestration service capable of integrating with multiple third-party AI providers.

---

## Architecture Overview

The backend is designed as a set of four independent but interconnected microservices, each with its own dedicated database and responsibilities:

1.  **User Service:** The gatekeeper. Handles all aspects of user identity, including registration with OTP email verification, secure login, and JWT token generation.
2.  **Billing Service:** The accountant. Manages user credit balances, seeds the system with the available AI models and their costs, and provides endpoints for credit deduction and transaction history.
3.  **Queue Service:** The job dispatcher. Authenticates user requests, validates them against the billing service, and places valid AI tasks into a reliable message queue for background processing.
4.  **Orchestration Service:** The engine room. A headless background worker that listens for new jobs, calls the appropriate third-party AI provider (OpenAI, Sarvam.ai, etc.), and updates the job status with the final result.
<!-- You can replace this with a link to your own diagram -->

---

## Technology Stack

This project leverages a modern, high-performance technology stack chosen for its scalability, reliability, and strong community support.

*   **Backend Framework:** [FastAPI](https://fastapi.tiangolo.com/)
*   **Programming Language:** Python 3.11+
*   **Databases:** [PostgreSQL](https://www.postgresql.org/)
*   **Message Broker:** [RabbitMQ](https://www.rabbitmq.com/)
*   **Asynchronous Communication:** `pika` for RabbitMQ integration
*   **Data Validation:** `Pydantic`
*   **Database ORM:** `SQLAlchemy`
*   **Authentication:** `passlib[bcrypt]` for password hashing, `python-jose` for JWT
*   **Email Sending:** `fastapi-mail` for OTP delivery

---

## Local Development Setup

Follow these steps to get the entire backend running on your local machine.

### Prerequisites

1.  **Python 3.11+:** Ensure Python is installed and added to your system's PATH.
2.  **PostgreSQL:** Install and run the PostgreSQL database server. During setup, create a user named `farmvidhya` with the password `password`.
3.  **RabbitMQ:** Install Erlang, then install the RabbitMQ server. Enable the management plugin by running `rabbitmq-plugins enable rabbitmq_management` in an administrator terminal.

### Step-by-Step Installation

1.  **Clone the Repository:**
    ```bash
    git clone <your-repository-url>
    cd FarmVidhya-Backend
    ```

2.  **Create Databases:**
    Connect to PostgreSQL (e.g., using `psql -U postgres`) and run the following commands to create the dedicated databases and assign ownership:
    ```sql
    CREATE DATABASE user_db OWNER farmvidhya;
    CREATE DATABASE billing_db OWNER farmvidhya;
    CREATE DATABASE queue_db OWNER farmvidhya;
    ```

3.  **Set Up Each Service:**
    For **each** of the four service directories (`user_service`, `billing_service`, `queue_service`, `orchestration_service`), you must perform the following steps in a **separate, dedicated terminal**:

    *   **Navigate to the service directory:**
        ```powershell
        cd path/to/service_directory
        ```
    *   **Create and activate a virtual environment:**
        ```powershell
        python -m venv venv
        .\venv\Scripts\Activate.ps1
        ```
    *   **Install dependencies:**
        ```powershell
        pip install -r requirements.txt
        ```

4.  **Configure Environment Variables:**
    *   In the `user_service` directory, create a `.env` file for your email credentials.
    *   In the `orchestration_service` directory, create a `.env` file for your AI provider API keys.
    *   Before running each service, you must set its required environment variables in the terminal (see the individual service `README.md` files for details).

5.  **Launch the Services:**
    Run the launch command in each of the four terminals.
    *   **Terminals 1, 2, 3 (API Services):** `uvicorn main:app --reload --port <port_number>`
    *   **Terminal 4 (Worker):** `python worker.py`

You now have the entire backend running and ready for testing or frontend integration!
