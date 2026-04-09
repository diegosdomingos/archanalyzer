from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock


def test_health():
    with patch("app.core.database.create_engine"), \
         patch("app.core.database.Base.metadata.create_all"):
        from app.main import app
        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


def test_report_not_found():
    with patch("app.core.database.create_engine"), \
         patch("app.core.database.Base.metadata.create_all"):
        from app.main import app
        client = TestClient(app)

        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = None

        with patch("app.routers.report.get_db", return_value=iter([mock_session])):
            response = client.get("/report/job-inexistente")

        assert response.status_code == 404
        assert "não encontrado" in response.json()["detail"]