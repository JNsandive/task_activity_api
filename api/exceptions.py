from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
import logging
from pydantic import BaseModel

app = FastAPI()
logger = logging.getLogger(__name__)


class ErrorResponse(BaseModel):
    detail: str


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(exc: SQLAlchemyError):
    logger.error(f"Database error occurred: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(detail="An error occurred while interacting with the database").dict()
    )


@app.exception_handler(HTTPException)
async def http_exception_handler( exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(detail=exc.detail).dict()
    )


@app.exception_handler(Exception)
async def general_exception_handler(exc: Exception):
    logger.error(f"Unexpected error occurred: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(detail="An unexpected error occurred").dict()
    )
