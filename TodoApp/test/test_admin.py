from .utils import *
from routers.admin import get_current_user, get_db
from main import app
from starlette import status

app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user] = override_get_current_user


def test_admin_read_all_authenticated(test_todo):
    response = client.get("/admin/todo")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == [
        {
            'id':1,
            "title": "Learn to Code!",
            "description": "Learn Everyday!",
            "priority": 5,
            "complete": False,
            "owner_id": 1,
        }
    ]


def test_admin_delete_todo(test_todo):
    response = client.delete("admin/delete/1")
    assert response.status_code == status.HTTP_204_NO_CONTENT

    db = TestingSessionLocal()
    model = db.query(Todos).filter(Todos.id == 1).first()

    assert model == None


def test_admin_delete_todo_not_found():
    response = client.delete("admin/delete/999")
    assert response.status_code == status.HTTP_404_NOT_FOUND
