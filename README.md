# FarmVidhya - Backend System Architecture

## 1. Overview

Welcome to the backend for the **FarmVidhya Conversational AI** platform. This is a complete, production-grade backend system designed from the ground up to be scalable, resilient, and maintainable. It handles all server-side logic, from user authentication and credit management to the complex, asynchronous processing of AI tasks.

This system is not a single application but a collection of four distinct **microservices** that communicate with each other to fulfill user requests, inspired by the architectures of modern, large-scale platforms like ElevenLabs.

---

## 2. Core Architectural Philosophy: Why Microservices?

The most important architectural decision for this project was to use a **Microservices Architecture** instead of a traditional **Monolith**.

In a monolith, all code (for users, billing, AI jobs, etc.) lives in one large, single application. This is simple to start but becomes incredibly difficult to manage and scale.

We chose microservices for these critical advantages:

*   **✅ Separation of Concerns:** Each service has a single, well-defined responsibility. The User Service knows nothing about AI models; the AI worker knows nothing about passwords. This makes the code for each service simpler, cleaner, and easier to understand.
*   **✅ Independent Scalability:** If our Speech-to-Text model becomes extremely popular, we can deploy 50 copies of the `orchestration_service` to handle the load without needing to scale any of the other services. This is vastly more cost-effective and efficient.
*   **✅ Resilience & Fault Isolation:** If a bug causes the `billing_service` to crash, it **does not** bring down the rest of the platform. Users can still sign up, log in, and submit jobs. The system is fundamentally more stable.
*   **✅ Technological Flexibility:** Each service is independent. We could, in the future, rewrite the `orchestration_service` in a language like Go or Rust for maximum performance without changing any other part of the system.

---

## 3. Technology Stack

This project leverages a modern, robust technology stack chosen for performance, reliability, and developer productivity.

*   **Language:** **Python 3.11+**
*   **Web Framework:** **FastAPI** (for its high performance, asynchronous capabilities, and automatic documentation)
*   **Database:** **PostgreSQL** (a powerful, open-source relational database)
*   **Database Interface (ORM):** **SQLAlchemy** (for writing Pythonic, safe, and maintainable database queries)
*   **Message Broker:** **RabbitMQ** (for managing the asynchronous job queue reliably)
*   **Security:**
    *   **Passlib (bcrypt):** For industry-standard, secure password hashing.
    *   **Python-JOSE:** For creating and validating JWT (JSON Web Tokens) for authentication.
*   **Data Validation:** **Pydantic** (for defining clear API contracts and validating all incoming data)

---

## 4. The Four Microservices

The backend is composed of four services, each with a distinct role.

###  GATEKEEPER 🔑: `user_service`
*   **Responsibility:** Manages all aspects of user identity. It handles user registration, validates credentials on login, and issues secure JWT access tokens. It is the single source of truth for "who a user is."
*   **Runs on Port:** `8001`

### ACCOUNTANT 💵: `billing_service`
*   **Responsibility:** Manages all logic related to user credits. It defines the "cost" for using different AI models, tracks each user's credit balance, and assigns initial free credits.
*   **Runs on Port:** `8002`

### JOB DISPATCHER 📨: `queue_service`
*   **Responsibility:** The main, authenticated entry point for all AI tasks. It validates the user's token, creates a persistent job record for tracking, and then hands off the actual work to the background system by placing a message on the queue.
*   **Runs on Port:** `8003`

### ENGINE ROOM ⚙️: `orchestration_service`
*   **Responsibility:** The background workhorse of the platform. This is a headless service (no API) that constantly listens for new jobs from the message queue. It performs the heavy, time-consuming AI processing, ensuring the main application remains fast and responsive.
*   **Runs as:** A background Python script.

---

## 5. The Complete End-to-End Workflow

This is how all four services work in concert to process a user's request from start to finish.

**Step 1: Authentication**
*   **Service:** `user_service`
*   **Action:** A user signs up and/or logs in via the `/signup` and `/login` endpoints.
*   **Result:** The user receives a **JWT Access Token**. This token is a secure key they must use for all future actions.

**Step 2: Job Submission**
*   **Service:** `queue_service`
*   **Action:** The user sends a request to the `/jobs` endpoint. They include the **JWT Access Token** in the `Authorization` header and provide the job details (e.g., `model_identifier`).
*   **Result:** The service validates the token, creates a `PENDING` job in its database, and instantly responds to the user with a unique **`job_id`**.

**Step 3: Asynchronous Hand-off**
*   **Technology:** `RabbitMQ`
*   **Action:** Immediately after creating the job record, the `queue_service` publishes a small message containing the **`job_id`** to the `ml_jobs` queue.
*   **Result:** The message is now waiting securely in the queue, guaranteed to be processed.

**Step 4: Background Processing**
*   **Service:** `orchestration_service`
*   **Action:** The worker, which is always listening, picks up the message from the queue. It uses the `job_id` to update the job's status to `PROCESSING`, performs the long-running AI task (currently simulated), and finally updates the status to `COMPLETED`.
*   **Result:** The job is finished, and the result (an output URL) is saved in the database.

**Step 5: Result Retrieval**
*   **Service:** `queue_service`
*   **Action:** The user, at any time, can make a request to the `GET /jobs/{job_id}` endpoint (providing their JWT token).
*   **Result:** The service reads the current status of the job from its database and returns it to the user. Once the status is `COMPLETED`, the response will also contain the final output URL.

---

## 6. Local Development Setup

Follow these steps to run the entire backend on your local machine.

### Prerequisites

You must have **Python**, **PostgreSQL**, and **RabbitMQ** installed and running on your system.

### Database Setup

Before launching any service, you must create the databases and the user. Connect to PostgreSQL with a superuser account (e.g., `postgres`) and run the following SQL commands:

```sql
-- Create a dedicated user for our application
CREATE USER farmvidhya WITH PASSWORD 'password';

-- Create the three databases and immediately assign our new user as the owner
CREATE DATABASE user_db OWNER farmvidhya;
CREATE DATABASE billing_db OWNER farmvidhya;
CREATE DATABASE queue_db OWNER farmvidhya;



Running the Services
Each service must be run in its own dedicated terminal. The general process for each is:
Navigate to the service directory (e.g., cd Backend/user_service).
Create and activate a Python virtual environment (python -m venv venv and .\venv\Scripts\Activate.ps1).
Install the required dependencies (pip install -r requirements.txt).
Set the required environment variables for that terminal session.
Run the server (uvicorn ...) or the worker (python worker.py).
Refer to the README.md file inside each service's folder for the exact commands.


7. Future Work & Next Steps
This project provides a solid foundation. The next logical steps to move towards a production deployment are:
Containerization: "Dockerizing" each service by creating a Dockerfile for it. This packages the service and all its dependencies into a portable container.
Orchestration: Using a tool like Docker Compose (for local development) or Kubernetes (for production) to manage the lifecycle of all the containers automatically.
CI/CD: Setting up a Continuous Integration/Continuous Deployment pipeline to automate testing and deployments.
