# Billing Service

**Role:** Accountant & Policy Manager

This service manages user credit balances and defines the available AI models and their costs.

## Features

*   **Automatic Credit Assignment:** Assigns 100 free credits to new users upon their first interaction.
*   **Credit Deduction:** Provides a secure endpoint for other services to deduct credits for completed jobs.
*   **Transaction History:** Records every deduction in a `transactions` table for auditing and provides an API to view this history.
*   **Dynamic Policy Seeding:** Automatically creates and updates the "menu" of available AI models and their costs in the database on startup.

## API Endpoints

*   `GET /balance/{user_id}`: Check a user's current credit balance.
*   `GET /policies`: Get a list of all available AI models and their costs.
*   `GET /policies/rules`: Get a list of the platform's credit usage rules.
*   `POST /transactions/deduct`: (Internal) Deduct credits from a user's account.
*   `GET /transactions/{user_id}`: Get a user's complete transaction history.

## Setup & Launch

1.  **Navigate to this directory** in a dedicated terminal.
2.  **Create and activate a virtual environment** and **install dependencies** as described in the main README.
3.  **Set Environment Variables:**
    ```powershell
    $env:DATABASE_URL = "postgresql://farmvidhya:password@localhost:5432/billing_db"
    ```
4.  **Launch the Service:**
    ```powershell
    uvicorn main:app --reload --port 8002
    ```
5.  **Access the API Docs:** `http://127.0.0.1:8002/docs`
