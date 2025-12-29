import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from .main import app
from .database import Base, get_db
from . import models, auth

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    # Create tables
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    
    # Pre-seed Admin User
    hashed_pw = auth.get_password_hash("admin")
    admin_user = models.User(
        username="admin", 
        hashed_password=hashed_pw,
        display_name="Administrator"
    )
    session.add(admin_user)
    
    # Pre-seed Categories (mimic main.py startup)
    categories = [
        models.Category(name="Alimentos", icon="🍎", color="#FF5733"),
        models.Category(name="Limpeza", icon="🧹", color="#33FF57"),
        models.Category(name="Higiene", icon="🧼", color="#3357FF"),
    ]
    session.add_all(categories)
    session.commit()
    
    yield session
    session.close()
    # Drop tables
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()

@pytest.fixture(scope="function")
def test_user(db_session):
    user = models.User(
        username="testuser",
        hashed_password=auth.get_password_hash("testpass"),
        display_name="Test User",
        language_preference="en-US",
        theme_preference="light"
    )
    db_session.add(user)
    db_session.commit()
    return user

@pytest.fixture(scope="function")
def auth_headers(client, test_user):
    response = client.post(
        "/token",
        data={"username": "testuser", "password": "testpass"}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
