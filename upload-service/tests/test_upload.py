from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@patch("app.routers.upload.aio_pika.connect_robust")
@patch("app.routers.upload.get_db")
def test_upload_invalid_file_type(mock_db, mock_rabbit):
    response = client.post(
        "/upload",
        files={"file": ("test.txt", b"conteudo", "text/plain")}
    )
    assert response.status_code == 400
    assert "não permitido" in response.json()["detail"]