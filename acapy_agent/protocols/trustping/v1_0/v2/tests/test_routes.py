"""Tests for TrustPing v1.0 Admin API v2 routes."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from acapy_agent.admin.fastapi_factory import create_admin_app
from acapy_agent.config.injection_context import InjectionContext
from acapy_agent.connections.models.conn_record import ConnRecord
from acapy_agent.core.profile import Profile
from acapy_agent.storage.error import StorageNotFoundError

# Using the TestClient allows us to test the FastAPI app synchronously
# while the underlying implementation is async.


@pytest.fixture
def mock_context():
    """Mock the InjectionContext."""
    context = MagicMock(spec=InjectionContext)
    context.settings = {
        "admin.admin_insecure_mode": True,  # Bypass auth for unit tests
        "default_label": "Test Agent",
    }
    return context


@pytest.fixture
def mock_profile(mock_context):
    """Mock the Profile."""
    profile = MagicMock(spec=Profile)
    profile.context = mock_context

    # Mock the session() async context manager
    session = AsyncMock()
    # When 'async with profile.session() as session' is called:
    profile.session.return_value.__aenter__.return_value = session
    return profile


@pytest.fixture
def mock_outbound_router():
    """Mock the outbound message router."""
    return AsyncMock()


@pytest.fixture
def client(mock_context, mock_profile, mock_outbound_router):
    """Create a TestClient with the configured Admin App."""
    app = create_admin_app(mock_context, mock_profile, mock_outbound_router)
    return TestClient(app)


class TestTrustPingRoutes:
    """Test TrustPing v2 routes."""

    @patch("acapy_agent.protocols.trustping.v1_0.v2.routes.ConnRecord")
    def test_send_ping_success(self, mock_conn_record, client, mock_outbound_router):
        """Test successful ping dispatch."""
        # 1. Arrange
        conn_id = "test-conn-id"
        mock_conn = MagicMock(spec=ConnRecord)
        mock_conn.is_ready = True
        mock_conn.connection_id = conn_id

        # Mock retrieve_by_id to return our mock connection
        mock_conn_record.retrieve_by_id = AsyncMock(return_value=mock_conn)

        # 2. Act
        response = client.post(
            f"/connections/{conn_id}/send-ping", json={"comment": "testing 123"}
        )

        # 3. Assert
        assert response.status_code == 200
        data = response.json()

        # Verify Pydantic camelCase serialization
        assert "threadId" in data

        # Verify DB lookup
        mock_conn_record.retrieve_by_id.assert_called_once()

        # Verify message sent via router
        mock_outbound_router.assert_awaited_once()

        # The outbound router is called with (profile, message)
        args = mock_outbound_router.call_args[0]
        assert len(args) == 2

        outbound_msg = args[1]
        # The payload is serialized JSON inside the OutboundMessage
        payload = json.loads(outbound_msg.payload)

        # Updated to expect fully qualified DIDComm message type
        assert payload["@type"] == "https://didcomm.org/trust_ping/1.0/ping"
        assert payload["comment"] == "testing 123"
        assert outbound_msg.connection_id == conn_id

    @patch("acapy_agent.protocols.trustping.v1_0.v2.routes.ConnRecord")
    def test_send_ping_not_found(self, mock_conn_record, client):
        """Test 404 when connection does not exist."""
        # 1. Arrange
        conn_id = "missing-conn-id"
        mock_conn_record.retrieve_by_id = AsyncMock(
            side_effect=StorageNotFoundError("Record not found")
        )

        # 2. Act
        response = client.post(f"/connections/{conn_id}/send-ping")

        # 3. Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Connection not found"

    @patch("acapy_agent.protocols.trustping.v1_0.v2.routes.ConnRecord")
    def test_send_ping_not_ready(self, mock_conn_record, client, mock_outbound_router):
        """Test 400 when connection is not ready/active."""
        # 1. Arrange
        conn_id = "pending-conn-id"
        mock_conn = MagicMock(spec=ConnRecord)
        mock_conn.is_ready = False  # Not active
        mock_conn_record.retrieve_by_id = AsyncMock(return_value=mock_conn)

        # 2. Act
        response = client.post(f"/connections/{conn_id}/send-ping")

        # 3. Assert
        assert response.status_code == 400
        assert f"Connection {conn_id} not ready" in response.json()["detail"]

        # Verify router was NOT called
        mock_outbound_router.assert_not_called()

    @patch("acapy_agent.protocols.trustping.v1_0.v2.routes.ConnRecord")
    def test_send_ping_router_missing_error(
        self, mock_conn_record, mock_context, mock_profile
    ):
        """Test 500 if outbound router is missing from app state."""
        # 1. Arrange - Manually create app WITHOUT router to simulate setup error
        # We don't use the 'client' fixture here because we need a broken app
        app = create_admin_app(mock_context, mock_profile, None)
        # Manually remove it if factory sets it (factory might strict type it, but for runtime safety check)
        del app.state.outbound_message_router

        client_broken = TestClient(app)

        mock_conn = MagicMock(spec=ConnRecord)
        mock_conn.is_ready = True
        mock_conn_record.retrieve_by_id = AsyncMock(return_value=mock_conn)

        # 2. Act
        response = client_broken.post("/connections/some-id/send-ping")

        # 3. Assert
        assert response.status_code == 500
        assert "Outbound message router not initialized" in response.json()["detail"]
