from fastapi import APIRouter
from pydantic import BaseModel,Field
from models import Users

router = APIRouter()

class CreateUserRequest(BaseModel):
    username : str = Field(min_length=5,max_length=20)
    email : str = Field()
    first_name : str = Field(min_length=5)
    last_name : str = Field(min_length=5)
    password : str
    role : str

@router.post("/auth")
async def get_user(create_user_request : CreateUserRequest):
    create_user_model = Users(
        email=create_user_request.email,
        username=create_user_request.username,
        first_name=create_user_request.first_name,
        last_name=create_user_request.last_name,
        role=create_user_request.role,
        hashed_password = create_user_request.password,
        is_active=True
    )

    return create_user_model














    return {'User' : "Authenticated"}