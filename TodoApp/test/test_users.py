from .utils import *
from models import Users
from starlette import status
from routers.users import get_db,get_current_user

app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user] = override_get_current_user


def test_users_get_user(test_user):
    response = client.get("/users/get-user")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()['username'] == "Rakib0ne8"
    assert response.json()["email"] == "rakib@email.com"
    assert response.json()["first_name"] == "Rakib"
    assert response.json()["last_name"] == "Mondal"
    assert response.json()["role"] == "admin"
    assert response.json()["is_active"] == True
    assert response.json()["phone_number"] == "9832760260"

    # {
    #     'id':1,
    #     'email':"rakib@email.com",
    #     'username':"Rakib0ne8",
    #     'first_name':"Rakib",
    #     'last_name':"Mondal",
    #     'role':"admin",
    #     'hashed_password':pwd_context.hash("rakib123"),
    #     'is_active':True,
    #     'phone_number':'9832760260',
    # }


def test_users_get_user_not_found():
    response = client.get("/users/get-user")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == None


def test_users_change_password(test_user):
    request_data = {
        'password':'rakib123',
        'new_password' : 'rakib12'
    }

    response = client.put("/users/change-password",json=request_data)
    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_users_change_password_invalid_current_password(test_user):
    request_data = {"password": "rakib12", "new_password": "rakib123"}

    response = client.put("/users/change-password", json=request_data)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {'detail' : 'Error on Password Change'}


def test_users_update_phone_number(test_user):
    request_data = {
        'phone_number' : '84357398143'
    }

    response = client.put("/users/update-phone_number",json=request_data)
    assert response.status_code == status.HTTP_204_NO_CONTENT

    db = TestingSessionLocal()
    model = db.query(Users).filter(Users.phone_number == request_data.get('phone_number')).first()

    assert model.phone_number == request_data.get('phone_number')

