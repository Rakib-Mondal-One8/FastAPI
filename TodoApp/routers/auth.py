from typing import Annotated
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from database import SessionLocal
from models import Users
from passlib.context import CryptContext
import hashlib
from starlette import status
from fastapi.security import OAuth2PasswordRequestForm


router = APIRouter()

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


class CreateUserRequest(BaseModel):
    username: str = Field(min_length=5, max_length=20)
    email: str = Field()
    first_name: str = Field(min_length=5)
    last_name: str = Field(min_length=5)
    password: str
    role: str


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]


def authenticate_user(username: str, password: str, db):
    user = db.query(Users).filter(Users.username == username).first()
    if not user:
        return False
    if not pwd_context.verify(password, user.hashed_password):
        return False

    return True


@router.post("/auth", status_code=status.HTTP_201_CREATED)
async def get_user(db: db_dependency, create_user_request: CreateUserRequest):
    create_user_model = Users(
        email=create_user_request.email,
        username=create_user_request.username,
        first_name=create_user_request.first_name,
        last_name=create_user_request.last_name,
        role=create_user_request.role,
        hashed_password=pwd_context.hash(create_user_request.password),
        is_active=True,
    )

    db.add(create_user_model)
    db.commit()


@router.post("/token")
async def Login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: db_dependency
):

    if not authenticate_user(form_data.username, form_data.password, db):
        return "Failed Authentication"
    else:
        return "Successful Authentication"
