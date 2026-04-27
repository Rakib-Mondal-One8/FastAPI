from typing import Annotated, Optional
from fastapi import Depends, HTTPException, Path, APIRouter, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from models import Todos
from database import SessionLocal
from starlette import status
from .auth import get_current_user
from fastapi.templating import Jinja2Templates
from starlette.responses import RedirectResponse

router = APIRouter(
	prefix="/todos",
	tags=["todos"])


def get_db():
	db = SessionLocal()
	try:
		yield db
	finally:
		db.close()


db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict(), Depends(get_current_user)]

templates = Jinja2Templates(directory='templates')


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


def redirect_to_login():
	redirect_response = RedirectResponse(url="/auth/login-page", status_code=status.HTTP_302_FOUND)
	redirect_response.delete_cookie(key="access_token")
	return redirect_response


### Pages ###

@router.get("/todo-page")
async def render_todo_page(request: Request, db: db_dependency):
	try:
		user = await get_current_user(request.cookies.get('access_token'))
		if user is None:
			return redirect_to_login()

		todos = db.query(Todos).filter(Todos.owner_id == user.get("id")).all()
		return templates.TemplateResponse(request, 'todo.html', {"todos": todos, "user": user})
	except:
		return redirect_to_login()


@router.get("/add-todo")
async def add_todo(request: Request, db: db_dependency):
	try:
		user = await get_current_user(request.cookies.get('access_token'))
		if user is None:
			return redirect_to_login()
		return templates.TemplateResponse(request, 'add-todo.html', {'user': user})
	except:
		return redirect_to_login()


@router.get("/edit-todo-page/{todo_id}")
async def edit_todo(request: Request, db: db_dependency, todo_id: int = Path(gt=0)):
	try:
		user = await get_current_user(request.cookies.get('access_token'))
		if user is None:
			return redirect_to_login()
		todo = db.query(Todos).filter(Todos.id == todo_id).first()
		return templates.TemplateResponse(request, 'edit-todo.html', {"todo": todo, "user": user})
	except:
		return redirect_to_login()


### Endpoints ###

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
		user: user_dependency, db: db_dependency, todo_id: int = Path(gt=0)  # type: ignore
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


@router.put("/update-todo/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def update_todo(
		user: user_dependency,  # type: ignore
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
		user: user_dependency, db: db_dependency, todo_id: int = Path(gt=0)  # type: ignore
):
	if not user:
		raise HTTPException(
			status_code=status.HTTP_401_UNAUTHORIZED,
			detail="Could not validate user.",
		)

	todo = db.query(Todos).filter(Todos.id == todo_id).filter(Todos.owner_id == user.get('id')).first()
	if todo is None:
		raise HTTPException(status_code=404, detail="Todo Not Found!")

	db.delete(todo)
	db.commit()
