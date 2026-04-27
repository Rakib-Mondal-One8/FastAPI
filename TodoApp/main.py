from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from database import engine
import models
from routers import auth, todos, admin, users
from fastapi.staticfiles import StaticFiles

app = FastAPI()

models.Base.metadata.create_all(bind=engine)

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def test(request: Request):
	return RedirectResponse("/todos/todo-page", status_code=302)


@app.get("/healthy")
def health_check():
	return {'status': 'Healthy'}


app.include_router(auth.router)
app.include_router(todos.router)
app.include_router(admin.router)
app.include_router(users.router)
