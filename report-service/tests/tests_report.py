from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@patch("app.routers.report.get_db")
def test_report_not_found(mock_db):
    mock_session = MagicMock()
    mock_session.query.return_value.filter.return_value.first.return_value = None
    mock_db.return_value = iter([mock_session])

    response = client.get("/report/job-inexistente")
    assert response.status_code == 404