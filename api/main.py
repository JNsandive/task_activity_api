from http.client import HTTPException
from logging.handlers import RotatingFileHandler

import uvicorn
from fastapi import FastAPI
from fastapi.exception_handlers import http_exception_handler
from sqlalchemy.exc import SQLAlchemyError
from starlette.middleware.cors import CORSMiddleware

from .exceptions import sqlalchemy_exception_handler, general_exception_handler
from .routers import tasks, users, task_history, auth, webhooks
from .database import Base, engine

import logging

# Configure logging
handler = RotatingFileHandler('app.log', maxBytes=20000000, backupCount=5)
logging.basicConfig(
    handlers=[handler],  # File handler
    level=logging.INFO,  # Log level
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  # Log format
    datefmt='%Y-%m-%d %H:%M:%S',  # Date format
)

# Initialize logger
logger = logging.getLogger(__name__)


# Create all database tables
Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust to the domain you're accessing from
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routers
app.include_router(tasks.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(task_history.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1")
# app.include_router(webhooks.router, prefix="/api")

# Register custom exception handlers
app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8000)
