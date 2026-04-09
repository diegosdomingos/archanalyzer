import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch

from app.core.database import Base
from app.routers.report import get_db

TEST_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def get_client():
    with patch("app.core.database.create_engine", return_value=engine):
        from app.main import app
        app.dependency_overrides[get_db] = override_get_db
        return TestClient(app)


def test_health():
    client = get_client()
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_report_not_found():
    client = get_client()
    response = client.get("/report/job-inexistente")
    assert response.status_code == 404
    assert "não encontrado" in response.json()["detail"]