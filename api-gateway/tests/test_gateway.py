from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@patch("app.routers.gateway.httpx.AsyncClient")
def test_upload_proxies_to_upload_service(mock_client):
    mock_response = AsyncMock()
    mock_response.json.return_value = {"job_id": "123", "status": "received"}
    mock_response.raise_for_status = AsyncMock()
    mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)

    with open("tests/test_image.png", "wb") as f:
        f.write(b"fake image content")

    with open("tests/test_image.png", "rb") as f:
        response = client.post("/api/v1/upload", files={"file": ("test.png", f, "image/png")})

    assert response.status_code == 200