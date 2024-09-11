import logging

from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from starlette import status

from .database import get_db
from .models import User
from .schemas import AccessToken

SECRET_KEY = "your_jwt_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


async def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


async def get_password_hash(password):
    return pwd_context.hash(password)


async def create_access_token(data: dict):
    try:
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

        response = AccessToken(
            access_token=encoded_jwt,
            token_type="bearer"
        )

        return response

    except Exception as e:
        logger.error(f"Error creating access token: {str(e)}")
        raise HTTPException(status_code=400, detail="Could not create access token")


# Function to authenticate user by querying the database and verifying the password
async def authenticate_user_and_create_token(db: Session, username: str, password: str):
    try:
        # Check if the user exists by querying the database
        user = db.query(User).filter(User.email == username).first()
        if not user or not await verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect username or password",
            )

        # create jwt token
        response = await create_access_token(data={"sub": str(user.id)})

        logger.info(f"Authentication successful for user: {username}")

        # Return the access token and token type (bearer)
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=response.dict()
        )
    except HTTPException as http_exc:
        logger.error(f"HTTP error during authentication for user {username}: {http_exc.detail}")
        raise http_exc

    except Exception as e:
        logger.error(f"Unexpected error during authentication for user {username}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during authentication"
        )


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    return user
