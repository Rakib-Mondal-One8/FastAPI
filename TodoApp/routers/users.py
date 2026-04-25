from typing import Annotated, Optional
from fastapi import Depends, HTTPException, Path, APIRouter
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from models import Todos
from database import SessionLocal
from starlette import status
from .auth import get_current_user
from models import Users
from passlib.context import CryptContext


router = APIRouter(prefix="/users", tags=["users"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict(), Depends(get_current_user)]
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


class UserVerification(BaseModel):
    password : str 
    new_password :str = Field(min_length=6)

class UpdatePhoneNumberRequest(BaseModel):
    phone_number: str = Field(min_length=10)

@router.get("/get-user",status_code=status.HTTP_200_OK)
async def get_user(user: user_dependency, db: db_dependency):
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication Failed")

    return db.query(Users).filter(Users.id == user.get("id")).first()


@router.put("/change-password",status_code=status.HTTP_204_NO_CONTENT)
async def change_password(user: user_dependency, db: db_dependency, user_verification: UserVerification):
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication Failed")

    user_model = db.query(Users).filter(Users.id == user.get('id')).first()

    if not pwd_context.verify(user_verification.password,user_model.hashed_password):
        raise HTTPException(status_code=401,detail='Error on Password Change')

    user_model.hashed_password = pwd_context.hash(user_verification.new_password)

    db.add(user_model)
    db.commit()


@router.put("/update-phone_number",status_code=status.HTTP_204_NO_CONTENT)
async def update_phoner_number(user:user_dependency,db:db_dependency,update_phone_number_request:UpdatePhoneNumberRequest):
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication Failed")
    
    user_model = db.query(Users).filter(Users.id == user.get('id')).first()

    user_model.phone_number = update_phone_number_request.phone_number
    db.add(user_model)
    db.commit()
