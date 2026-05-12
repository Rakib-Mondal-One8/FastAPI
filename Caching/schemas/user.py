from pydantic import BaseModel,Field


class User(BaseModel):
    id: int = Field(gt=0)
    name: str = Field(min_length=5)
    role: str