from __future__ import annotations
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from main import app
from model.models import Base
from database.database import get_db as real_get_db

# Use in-memory SQLite for tests
TEST_DATABASE_URL = "sqlite+pysqlite:///:memory:"  # requires SQLAlchemy 2.x default driver
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create all tables once per test session
@pytest.fixture(scope="session", autouse=True)
def create_tables():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

# Provide a fresh DB session per test
@pytest.fixture()
def db_session():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()

# Override FastAPI dependency
@app.dependency_overrides[real_get_db]  # type: ignore[index]
def override_get_db():  # pragma: no cover
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()

@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c
