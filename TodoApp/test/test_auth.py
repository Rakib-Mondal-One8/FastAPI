from datetime import datetime, timedelta, timezone

from .utils import *
from starlette import status
from routers.auth import get_db,authenticate_user,create_access_token,SECRET_KEY,ALGORITHM
from jose import jwt


app.dependency_overrides[get_db] = override_get_db

def test_authenticate_user(test_user):
    db = TestingSessionLocal()

    authenticated_user = authenticate_user(test_user.username,'rakib123',db)
    assert authenticated_user is not None
    assert authenticated_user.username == test_user.username


def test_create_access_token(test_user):

    token = create_access_token(test_user.username,test_user.id,test_user.role,timedelta(minutes=20))

    decoded_token = jwt.decode(token,SECRET_KEY,algorithms=[ALGORITHM],options={'verify_signature':False})

    assert decoded_token['sub'] == test_user.username
    assert decoded_token['id'] == test_user.id
    assert decoded_token["role"] == test_user.role

# def test_auth_create_user(test_user):
#     request_data = {
#         'email':"rakib@email.com",
#         'username':"Rakib0ne8",
#         'first_name':"Rakib",
#         'last_name':"Mondal",
#         'role':"admin",
#         'password':"rakib123",
#         'is_active':True,
#         'phone_number':'9832760260',
#     }

#     response = client.post("/auth/",json=request_data)
#     assert response.status_code == status.HTTP_201_CREATED


# def test_auth_Login_for_access_token(test_user):
#     request_data = {
#         'username' : 'Rakib0ne8',
#         'password' : 'rakib123'
#     }

#     response = client.post("/auth/token",json=request_data)
#     assert response.json() == {"access_token": 'token', "token_type": "bearer"}
