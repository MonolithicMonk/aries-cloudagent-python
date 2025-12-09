"""Tests for Admin API dependencies."""

from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException, Request

from ..dependencies import verify_admin_key


@pytest.fixture
def mock_request():
    """Mock FastAPI Request."""
    req = MagicMock(spec=Request)
    req.url.path = "/protected"
    req.method = "GET"
    return req


@pytest.mark.asyncio
async def test_verify_admin_key_success(mock_request):
    """Test successful API key verification."""
    settings = {"admin.admin_api_key": "secret"}
    # Should not raise exception
    await verify_admin_key(mock_request, "secret", settings)


@pytest.mark.asyncio
async def test_verify_admin_key_fail(mock_request):
    """Test failed API key verification."""
    settings = {"admin.admin_api_key": "secret"}

    with pytest.raises(HTTPException) as exc:
        await verify_admin_key(mock_request, "wrong", settings)
    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_verify_admin_key_public_paths(mock_request):
    """Test allowlist for public paths."""
    settings = {"admin.admin_api_key": "secret"}

    public_paths = [
        "/health",
        "/api/doc",
        "/api/docs/swagger.json",
        "/",  # Root redirect
    ]

    for path in public_paths:
        mock_request.url.path = path
        # Should not raise despite empty API key
        await verify_admin_key(mock_request, "", settings)


@pytest.mark.asyncio
async def test_verify_admin_key_options_method(mock_request):
    """Test CORS pre-flight OPTIONS request bypass."""
    mock_request.method = "OPTIONS"
    settings = {"admin.admin_api_key": "secret"}
    # Should not raise
    await verify_admin_key(mock_request, "", settings)


@pytest.mark.asyncio
async def test_verify_admin_key_insecure_mode(mock_request):
    """Test insecure mode bypass."""
    settings = {"admin.admin_insecure_mode": True}
    # Should not raise
    await verify_admin_key(mock_request, "", settings)
