# User Service

**Role:** Gatekeeper & Identity Manager

This service handles all user authentication and registration workflows.

## Features

*   **User Sign-up:** Creates a new, inactive user account.
*   **OTP Verification:** Generates a 6-digit OTP, securely stores its hash, and sends it to the user's email for account verification.
*   **Secure Login:** Authenticates active users with their email and password.
*   **JWT Generation:** Creates secure JSON Web Tokens for authenticated users to access other services.

## API Endpoints

*   `POST /signup`: Register a new user.
*   `POST /verify-otp`: Verify an account using the OTP sent via email.
*   `POST /login`: Log in to receive a JWT access token.

## Setup & Launch

1.  **Navigate to this directory** in a dedicated terminal.
2.  **Create and activate a virtual environment:**
    ```powershell
    python -m venv venv
    .\venv\Scripts\Activate.ps1
    ```
3.  **Install dependencies:**
    ```powershell
    pip install -r requirements.txt
    ```
4.  **Create `.env` file:**
    Create a file named `.env` in this directory and add your SMTP credentials:
    ```env
    MAIL_USERNAME=your-email@gmail.com
    MAIL_PASSWORD=your_16_character_app_password
    MAIL_FROM=your-email@gmail.com
    MAIL_PORT=587
    MAIL_SERVER=smtp.gmail.com
    ```
5.  **Set Environment Variables:**
    ```powershell
    $env:DATABASE_URL = "postgresql://farmvidhya:password@localhost:5432/user_db"
    $env:SECRET_KEY = "a-strong-secret-key-for-your-project"
    $env:ALGORITHM = "HS256"
    ```
6.  **Launch the Service:**
    ```powershell
    uvicorn main:app --reload --port 8001
    ```
7.  **Access the API Docs:** `http://127.0.0.1:8001/docs`
