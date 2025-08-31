# Billing Service

## Description

This service acts as the **Accountant** for the FarmVidhya platform. It is responsible for managing user credit balances and defining the "cost" of using the various AI models available.

## Tech Stack & Core Dependencies

*   **Framework:** FastAPI
*   **Database:** PostgreSQL with SQLAlchemy (ORM)

## Core Concepts & Flow

The service is designed to be simple and robust, handling credit policies and user balances.

1.  **Startup Seeding:** When the service starts, a special `lifespan` event is triggered. This function connects to the database and creates a set of predefined `CreditPolicy` records if they do not already exist. This ensures that the costs for models like `TELUGU_SST_V1` are always available in the system.

2.  **On-Demand Balance Creation:** The service implements a "lazy-loading" approach for user balances. The first time any part of the system requests a user's balance, the `get_user_balance` function checks if a record exists for that `user_id`. If it does not, a new `UserBalance` record is automatically created with the default **10,000 free credits**. This avoids having to create a balance record for every single user at sign-up.

## API Endpoints

*   `GET /policies`: Returns a list of all active credit policies and their costs.
*   `GET /balance/{user_id}`: Returns the current credit balance for a specific user. Creates a free credit balance if one does not exist.
*   `GET /docs`: Interactive API documentation.

## How to Run Locally

1.  **Navigate to Directory:** `cd Backend/billing_service`
2.  **Create & Activate Venv:**
    ```bash
    python -m venv venv
    .\venv\Scripts\Activate.ps1
    ```
3.  **Install Dependencies:** `pip install -r requirements.txt`
4.  **Set Environment Variable (PowerShell):**
    ```powershell
    $env:DATABASE_URL = "postgresql://farmvidhya:password@localhost:5432/billing_db"
    ```
5.  **Run Server:** `uvicorn main:app --reload --port 8002`
