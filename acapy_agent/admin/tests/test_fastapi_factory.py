"""Tests for FastAPI Factory."""

from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from ..fastapi_factory import create_admin_app


@pytest.fixture
def client():
    """Create a TestClient with a mocked context."""
    context = MagicMock()
    # Configure settings for Auth dependency to pass public routes
    context.settings = {"default_label": "Test Agent", "admin.admin_api_key": "secret"}
    profile = MagicMock()

    app = create_admin_app(context, profile)
    return TestClient(app)


def test_health_check(client):
    """Test the public health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_root_redirect(client):
    """Test that root redirects to legacy docs URL."""
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/api/doc"


def test_legacy_docs_url(client):
    """Test that the legacy docs URL is accessible."""
    response = client.get("/api/doc")
    assert response.status_code == 200
    assert "Swagger UI" in response.text
