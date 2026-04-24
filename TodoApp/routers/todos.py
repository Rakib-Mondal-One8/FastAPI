from typing import Annotated, Optional
from fastapi import Depends, HTTPException, Path, APIRouter
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from models import Todos
from database import SessionLocal
from starlette import status
from .auth import get_current_user

router = APIRouter(tags=["todos"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict(), Depends(get_current_user)]


class TodoRequest(BaseModel):
    title: str = Field(min_length=5)
    description: str = Field(min_length=5, max_length=100)
    priority: int = Field(gt=0, lt=6)
    complete: bool = Field(gt=-1, lt=2)

    model_config = {
        "json_schema_extra": {
            "example": {
                "title": "Task title",
                "description": "Task Description",
                "priority": 5,
                "complete": 0,
            }
        }
    }


@router.get("/", status_code=status.HTTP_200_OK)
async def read_all(user: user_dependency, db: db_dependency):  # type: ignore
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate user.",
        )
    return db.query(Todos).filter(Todos.owner_id == user.get("id")).all()


@router.get("/todo/{todo_id}", status_code=status.HTTP_200_OK)
async def read_todo(
    user: user_dependency, db: db_dependency, todo_id: int = Path(gt=0)
):
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate user.",
        )

    todo_model = (
        db.query(Todos)
        .filter(Todos.id == todo_id)
        .filter(Todos.owner_id == user.get("id"))
        .first()
    )
    if todo_model is not None:
        return todo_model
    raise HTTPException(status_code=404, detail="Todo not found!")


@router.post("/create-todo", status_code=status.HTTP_201_CREATED)
async def create_todo(
    user: user_dependency, db: db_dependency, todo_request: TodoRequest  # type: ignore
):
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate user.",
        )

    new_todo = Todos(**todo_request.model_dump(), owner_id=user.get("id"))
    db.add(new_todo)
    db.commit()
    return new_todo


@router.put("/update-todo/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def update_todo(
    user: user_dependency,
    db: db_dependency,
    todo_request: TodoRequest,
    todo_id: int = Path(gt=0),
):
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate user.",
        )
    todo_model = (
        db.query(Todos)
        .filter(Todos.id == todo_id)
        .filter(Todos.owner_id == user.get("id"))
        .first()
    )

    if todo_model is None:
        raise HTTPException(status_code=404, detail="Todo Not Found!")

    todo_model.title = todo_request.title
    todo_model.description = todo_request.description
    todo_model.priority = todo_request.priority
    todo_model.complete = todo_request.complete
    todo_model.owner_id = user.get("id")

    db.add(todo_model)
    db.commit()


@router.delete("/delete-todo/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(
    user: user_dependency, db: db_dependency, todo_id: int = Path(gt=0)
):
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate user.",
        )
    
    todo = db.query(Todos).filter(Todos.id == todo_id).filter(Todos.owner_id==user.get('id')).first()
    if todo is None:
        raise HTTPException(status_code=404, detail="Todo Not Found!")

    db.delete(todo)
    db.commit()
