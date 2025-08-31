
# User Service

## Description

This service acts as the **Gatekeeper** for the entire FarmVidhya platform. Its sole responsibility is to manage user identity, including registration, login, and the creation of secure authentication tokens (JWTs). It is the authoritative source for "who a user is."

## Tech Stack & Core Dependencies

*   **Framework:** FastAPI
*   **Database:** PostgreSQL with SQLAlchemy (ORM)
*   **Security:**
    *   `passlib[bcrypt]` for secure password hashing.
    *   `python-jose[cryptography]` for creating and managing JWTs.
    *   `email-validator` for validating email formats via Pydantic.

## Core Concepts & Flow

This service implements a standard and secure token-based authentication workflow.

1.  **Sign-up Flow (`POST /signup`):**
    *   A user submits their email and password.
    *   The service validates that the email is correctly formatted.
    *   It checks the database to ensure the email is not already in use.
    *   The plain-text password is put through the **bcrypt hashing algorithm** via `passlib`.
    *   The user's email and the **hashed password** are stored in the `users` table. The plain-text password is never stored.

2.  **Login Flow (`POST /login`):**
    *   A user submits their email and password.
    *   The service finds the user in the database by their email.
    *   It uses `passlib` to compare the submitted password against the stored hash.
    *   If they match, it uses `python-jose` to create a digitally signed **JSON Web Token (JWT)**. This token contains the user's ID and an expiration time.
    *   This JWT is returned to the user. The user must include this token in the `Authorization` header of all future requests to other services to prove their identity.

## API Endpoints

*   `POST /signup`: Register a new user.
*   `POST /login`: Authenticate a user and receive a JWT access token.
*   `GET /docs`: Interactive API documentation.

## How to Run Locally

1.  **Navigate to Directory:** `cd Backend/user_service`
2.  **Create & Activate Venv:**
    ```bash
    python -m venv venv
    .\venv\Scripts\Activate.ps1
    ```
3.  **Install Dependencies:** `pip install -r requirements.txt`
4.  **Set Environment Variables (PowerShell):**
    ```powershell
    $env:DATABASE_URL = "postgresql://farmvidhya:password@localhost:5432/user_db"
    $env:SECRET_KEY = "a_very_secret_key_for_jwt_tokens"
    $env:ALGORITHM = "HS256"
    $env:ACCESS_TOKEN_EXPIRE_MINUTES = "60"
    ```
5.  **Run Server:** `uvicorn main:app --reload --port 8001`
