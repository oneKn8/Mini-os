"""
API integration tests
"""

import os
import pytest
from fastapi.testclient import TestClient

from backend.api.server import app

client = TestClient(app)


def test_health_check():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_root_endpoint():
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert "service" in response.json()


@pytest.mark.skipif(not os.getenv("DATABASE_URL"), reason="Database not configured")
def test_inbox_endpoint():
    """Test inbox endpoint (may be empty)."""
    response = client.get("/api/inbox")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="OPENAI_API_KEY not set")
def test_planner_endpoint():
    """Test planner endpoint."""
    response = client.get("/api/planner/today")
    assert response.status_code == 200
    data = response.json()
    assert "must_do_today" in data or data == {}


@pytest.mark.skipif(not os.getenv("DATABASE_URL"), reason="Database not configured")
def test_pending_actions():
    """Test pending actions endpoint."""
    response = client.get("/api/actions/pending")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
