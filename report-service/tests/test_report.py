from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_report_not_found():
    mock_session = MagicMock()
    mock_session.query.return_value.filter.return_value.first.return_value = None

    with patch("app.routers.report.get_db", return_value=iter([mock_session])):
        response = client.get("/report/job-inexistente")

    assert response.status_code == 404
    assert "não encontrado" in response.json()["detail"]