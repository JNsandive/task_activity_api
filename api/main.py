from http.client import HTTPException

from fastapi import FastAPI
from fastapi.exception_handlers import http_exception_handler
from sqlalchemy.exc import SQLAlchemyError
from starlette.middleware.cors import CORSMiddleware

from .exceptions import sqlalchemy_exception_handler, general_exception_handler
from .routers import tasks, users, task_history, auth, webhooks
from .database import Base, engine

import logging


# Create all database tables
Base.metadata.create_all(bind=engine)

app = FastAPI()
logger = logging.getLogger("global_exception_handler")

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

# Global Exception Handler
# @app.exception_handler(Exception)
# async def global_exception_handler(request: Request, exc: Exception):
#     logger.critical(f"Unexpected error: {exc}")
#     return JSONResponse(
#         status_code=500,
#         content={"detail": "An unexpected error occurred. Please try again later."}
#     )

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("app.log"),
    ]
)