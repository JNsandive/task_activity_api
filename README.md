# Project Name

A brief description of your project.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Setting up Environment Variables](#2-set-up-a-virtual-environment)
- [Important: Setting Up SMTP Credentials (Google App Passwords)](#important-setting-up-smtp-credentials-google-app-passwords)
- [Running Migrations](#running-migrations)
- [Running the Application](#running-the-application)
- [API Documentation](#api-documentation)

---

## Prerequisites

Before running the project, make sure you have the following installed on your machine:

- **Python 3.8+**
- **PostgreSQL** (or any other database you are using)
- **Git** (for cloning the repository)

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/JNsandive/task_activity_api.git
cd project-name
```
### 2. Set Up a Virtual Environment

#### On MacOS/Linux
```bash
python3 -m venv venv
source venv/bin/activate
```

#### On Windows
```bash
python -m venv venv
.\venv\Scripts\activate
```
### 3. Install the required packages
```bash
pip install -r requirements.txt
```
### 4. Set Up the Database
```bash
# Login to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE your_database_name;
```

## Setting up Environment Variables
In the root directory of the project, create a `.env` file and add the following environment variables:
```python
DATABASE_URL="<postgresql://username:password@localhost:5432/your_database_name>"
SECRET_KEY="<your_secret_key_here>"
```
### Important: Setting Up SMTP Credentials (Google App Passwords)

This project requires you to set up SMTP credentials using **Google App Passwords** to send emails through the webhook. **Without these credentials, the webhook functionality will not work.**

### What You Need to Do:

1. **Generate a Google App Password**:
    - Go to your Google Account settings.
    - Navigate to **Security**.
    - Under **Signing in to Google**, select **App passwords**.
    - Generate a new app password for **Mail**.
   - **Or Directly head to this link**:- https://myaccount.google.com/apppasswords
   

2. **Add Environment Variables**:
    - Once you have your Google App Password, you **must** add the following environment variables in your `.env` file or system environment variables:

    ```bash
    SMTP_USERNAME=<your-google-email>
    SMTP_PASSWORD=<your-app-password>
    ```

    - Replace `<your-google-email>` with your Gmail address.
    - Replace `<your-app-password>` with the Google App Password you generated.

3. **Ensure the Environment Variables are Set**:
    - These variables are **required** for the webhook to work on your machine. Make sure the `SMTP_USERNAME` and `SMTP_PASSWORD` are correctly configured before running the project.

### Why This is Important:
The `SMTP_USERNAME` and `SMTP_PASSWORD` provide authentication for the Google SMTP server, which is necessary to send emails. If these credentials are not set up, the webhook will fail to send any emails.

## Running Migrations
#### 1. Initialize the Database (if migrations haven't been set up already):
```bash
alembic init alembic
```
#### 2. Apply Migrations:

```bash
alembic upgrade head
```
#### 3. Running New Migrations (if you modify the database schema):
```bash
alembic revision --autogenerate -m "Your migration message"
```
```bash 
alembic upgrade head
```

## Running the Application
After setting up the database and applying migrations, you can now run the application.

#### 1. Start the Application.
You can start the application using uvicorn:


```bash 
uvicorn api.main:app --reload
```
The application will be available at http://127.0.0.1:8000.

#### 2. Running the Application with the Main Entry:
```python 
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="127.0.0.1", port=8000, reload=True)
```

## API Documentation
### FastAPI automatically generates interactive API documentation, which you can access at:

- Swagger UI: http://127.0.0.1:8000/docs

- ReDoc: http://127.0.0.1:8000/redoc