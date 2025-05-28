# Flask API

A secure authentication system built with Flask, featuring JWT-based authentication, role-based access control, and email verification.

## Features

- ✅ User registration
- ✅ JWT-based authentication
- ✅ Role-based access control (Admin/User)
- ✅ Password reset functionality on Mail
- ✅ Two Factor Authentication using Google Authenticator 
- ✅ Scheduler to clear the Blacklist Token 
- ✅ Seeder for Creating the Admin
- ✅ Comprehensive logging

## Prerequisites

- Python 3.9+
- Mongodb
- Mail server credentials (MailTrap, etc.)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/flask-auth-api.git
   cd flask-auth-api

2. Create and activate a virtual environment:
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate

3. Install dependencies:
    ```bash
    pip install -r requirements.txt

4. Set up environment variables:
    ```bash
    cp .env.example .env

Edit the .env file with your configuration.

## Database Setup
Create your database (Mongodb)

1. Seed initial admin user 
    ```bash
    python3 -m seed.create_admin

## Running the Application

1. For development:
    ```bash
    flask run --debug

## Development Tools

1. Code Quality Checks
    To check formatting/linting 
    ```bash
    black . --check         # Checks Black formatting
    isort . --check-only    # Checks import sorting
    ruff check .            # Checks code quality and linting

2. Auto-fix Formatting and Linting
    ```bash
    To apply automatic fixes:
    black .                     # Formats code with Black
    isort .                     # Sorts imports
    ruff check . --fix          # Fixes issues Ruff can auto-correct

TO Test Pre commit config file => (.pre-commit-config-yaml)
```bash
    pre-commit clean
    pre-commit install
    pre-commit run --all-files
```

If you want to make a commit without running the pre-commit hooks (bypassing checks), use:
```bash
    git commit -m "commit message" --no-verify
```