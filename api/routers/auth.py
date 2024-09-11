from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from ..database import get_db
from ..auth_impl import authenticate_user_and_create_token

router = APIRouter()


@router.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # authenticate the user and return the token response
    token_response = await authenticate_user_and_create_token(db, form_data.username, form_data.password)

    return token_response

