import logging
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from starlette import status

from .models import User
from .schemas import UserCreate, UserCreatedResponse, UserResponse
from .auth_impl import get_password_hash

# Initialize the logger
logger = logging.getLogger(__name__)


# Create user
def create_user(db: Session, user_data: UserCreate):
    try:
        # Check if the email already exists in the database
        existing_user = db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            logger.warning(f"Attempt to create user with existing email: {user_data.email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email is already registered",
            )

        # Hash the password
        hashed_password = get_password_hash(user_data.password)

        # Create a new user
        db_user = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=hashed_password,
            is_admin=user_data.is_admin,
            company=user_data.company,
            picture_id=user_data.picture_id,
        )

        db.add(db_user)
        db.commit()
        db.refresh(db_user)

        logger.info(f"User created successfully: {db_user.email}")

        response = UserCreatedResponse(
            message="User created successfully",
            user=UserResponse(
                username=db_user.username,
                email=db_user.email,
            )
        )

        # Return the created user details with a success message and HTTP 201 status
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=response.dict()
        )
    except HTTPException as http_exc:
        logger.error(f"HTTP error during user creation: {str(http_exc.detail)}")
        raise http_exc

    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error during user creation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating the user"
        )
    except Exception as e:
        logger.critical(f"Unexpected error during user creation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )


# Get user by ID
def get_user(db: Session, user_id: int):
    try:
        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            logger.warning(f"User with ID {user_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found"
            )

        return user
    except HTTPException as http_exc:
        logger.error(f"HTTP error while fetching user ID {user_id}: {str(http_exc.detail)}")
        raise http_exc

    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error while fetching user ID {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while fetching the user"
        )
    except Exception as e:
        logger.critical(f"Unexpected error while fetching user ID {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )


# Get all users
def get_users(db: Session, skip: int = 0, limit: int = 10):
    try:
        users = db.query(User).offset(skip).limit(limit).all()

        if not users:
            logger.info("No users found in the database")
            return []

        return users

    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error while fetching users: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while fetching the users"
        )
    except Exception as e:
        logger.critical(f"Unexpected error while fetching users: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )
