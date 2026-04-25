from sqlalchemy import create_engine, text
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker
from database import Base
from main import app
from fastapi.testclient import TestClient
from pytest import fixture
from models import Todos,Users
from routers.auth import pwd_context


SQLALCHEMY_DATABASE_URL = "sqlite:///./testdb.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def override_get_current_user():
    return {"username": "RakibOne8test", "id": 1, "user_role": "admin"}


client = TestClient(app)


@fixture
def test_todo():
    todo = Todos(
        title="Learn to Code!",
        description="Learn Everyday!",
        priority=5,
        complete=False,
        owner_id=1,
    )

    db = TestingSessionLocal()
    db.add(todo)
    db.commit()
    yield todo
    with engine.connect() as connection:
        connection.execute(text("DELETE FROM todos;"))
        connection.commit()

@fixture
def test_user():
    user = Users(
        email="rakib@email.com",
        username="Rakib0ne8",
        first_name="Rakib",
        last_name="Mondal",
        role="admin",
        hashed_password=pwd_context.hash("rakib123"),
        is_active=True,
        phone_number='9832760260',
    )

    db = TestingSessionLocal()
    db.add(user)
    db.commit()

    yield user
    with engine.connect() as connection:
        connection.execute(text("DELETE FROM users;"))
        connection.commit()
