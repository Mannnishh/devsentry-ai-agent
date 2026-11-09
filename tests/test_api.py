"""Unit tests for FastAPI REST and SSE streaming endpoints."""

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from src.api.server import app

client = TestClient(app)


def test_health_check() -> None:
    """Verify /health endpoint returns 200 and correct service payload."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "service": "DevSentry",
        "version": "0.1.0",
    }


def test_agent_run_missing_task_param() -> None:
    """Verify /agent/run requires the 'task' query parameter."""
    response = client.get("/agent/run")
    assert response.status_code == 422


def test_agent_run_success() -> None:
    """Verify /agent/run executes task and returns JSON result."""
    mock_engine = MagicMock()
    mock_engine.run.return_value = "Mocked test answer."

    with patch("src.api.server.get_engine", return_value=mock_engine):
        response = client.get("/agent/run?task=List+files")
        assert response.status_code == 200
        data = response.json()
        assert data["task"] == "List files"
        assert data["result"] == "Mocked test answer."
        assert data["session_id"].startswith("api_")


def test_agent_stream_sse() -> None:
    """Verify /agent/stream returns Server-Sent Events content stream."""
    mock_engine = MagicMock()
    mock_engine.run.return_value = "Mocked stream answer."

    with patch("src.api.server.get_engine", return_value=mock_engine):
        response = client.get("/agent/stream?task=Analyze+code")
        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]
        body = response.text
        assert '{"event": "start"' in body
        assert '{"event": "finish"' in body
        assert "Mocked stream answer." in body
