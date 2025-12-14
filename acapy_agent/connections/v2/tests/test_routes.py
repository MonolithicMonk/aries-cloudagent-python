from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from acapy_agent.admin.fastapi_factory import create_admin_app
from acapy_agent.connections.models.conn_record import ConnRecord
from acapy_agent.connections.routes import ConnRecordSchema as LegacyConnRecordSchema
from acapy_agent.connections.v2.models import ConnRecordSchema as V2ConnRecordSchema
from acapy_agent.protocols.coordinate_mediation.v1_0.route_manager import RouteManager
from acapy_agent.protocols.coordinate_mediation.v1_0.route_manager_provider import (
    RouteManagerProvider,
)
from acapy_agent.resolver.did_resolver import DIDResolver
from acapy_agent.utils.testing import create_test_profile
from acapy_agent.wallet.did_method import DIDMethods
from acapy_agent.wallet.key_type import KeyTypes


@pytest.fixture
async def profile():
    """Create a test profile."""
    profile = await create_test_profile(
        settings={
            "admin.admin_insecure_mode": True,
            "wallet.type": "askar",
            "auto_provision": True,
            "wallet.key": "5BngFuBpS4wjFfVFCtPqoix3ZXG2XR8XJ7qosUzMak7R",
            "wallet.key_derivation_method": "RAW",
        }
    )

    # Inject dependencies required by BaseConnectionManager and Wallet
    profile.context.injector.bind_provider(RouteManager, RouteManagerProvider(profile))
    profile.context.injector.bind_instance(DIDMethods, DIDMethods())
    profile.context.injector.bind_instance(KeyTypes, KeyTypes())

    # Mock DIDResolver to avoid ledger lookups
    mock_resolver = MagicMock(spec=DIDResolver)

    # Mock resolve return value
    async def mock_resolve(profile, did, service_accept=None):
        return {
            "@context": "https://w3id.org/did/v1",
            "id": did,
            "verificationMethod": [
                {
                    "id": f"{did}#key-1",
                    "type": "Ed25519VerificationKey2018",
                    "controller": did,
                    "publicKeyBase58": "3Dn1SJNPaCXcvvJvSbsFWP2xaCjMom3can8LtaK3adDT",
                }
            ],
            "service": [
                {
                    "id": f"{did}#did-communication",
                    "type": "did-communication",
                    "serviceEndpoint": "http://example.com",
                    "recipientKeys": [f"{did}#key-1"],
                    "priority": 0,
                }
            ],
        }

    mock_resolver.resolve = mock_resolve

    # Mock dereference_verification_method
    async def mock_dereference(profile, uri, document=None):
        from pydid.verification_method import Ed25519VerificationKey2018

        return Ed25519VerificationKey2018(
            id=uri,
            type="Ed25519VerificationKey2018",
            controller=uri.split("#")[0],
            public_key_base58="3Dn1SJNPaCXcvvJvSbsFWP2xaCjMom3can8LtaK3adDT",
        )

    mock_resolver.dereference_verification_method = mock_dereference

    profile.context.injector.bind_instance(DIDResolver, mock_resolver)

    return profile


@pytest.fixture
async def client(profile):
    """Create a test client."""

    async def mock_outbound(*args, **kwargs):
        pass

    app = create_admin_app(profile.context, profile, mock_outbound)
    return TestClient(app)


def test_schema_parity():
    """Automated Schema Audit: Marshmallow vs Pydantic."""
    legacy_fields = LegacyConnRecordSchema().fields
    v2_fields = V2ConnRecordSchema.model_fields

    legacy_keys = set(legacy_fields.keys())
    v2_keys = set(v2_fields.keys())

    # BaseRecord fields are implicit in legacy inheritance but explicit in Pydantic
    ignored = {"created_at", "updated_at"}

    missing_in_v2 = (legacy_keys - v2_keys) - ignored
    missing_in_legacy = (v2_keys - legacy_keys) - ignored

    assert not missing_in_v2, (
        f"V2 Model missing fields present in Legacy: {missing_in_v2}"
    )
    # Note: We allow V2 to have extra fields if necessary (e.g. enhanced metadata),
    # but strictly speaking we want exact match for now.
    assert not missing_in_legacy, (
        f"Legacy Model missing fields present in V2: {missing_in_legacy}"
    )


@pytest.mark.asyncio
async def test_kitchen_sink_roundtrip(profile, client):
    """High-Fidelity Switch Test: Full field population."""
    # 1. Create a "Kitchen Sink" record using internal model
    # Populating ALL optional fields to ensure no data loss
    async with profile.session() as session:
        conn = ConnRecord(
            my_did="did:sov:123",
            their_did="did:sov:456",
            their_label="Label",
            their_role=ConnRecord.Role.REQUESTER.rfc160,
            invitation_key="3Dn1SJNPaCXcvvJvSbsFWP2xaCjMom3can8LtaK3adDT",
            invitation_msg_id="7e954593-6b71-4603-9b87-d421d84f686d",
            request_id="8f595615-de73-439d-9153-62a8d2cc559a",
            state=ConnRecord.State.COMPLETED.rfc160,
            inbound_connection_id="0963c744-c4a8-4150-b646-8329ff06717c",
            error_msg="Test error",
            accept=ConnRecord.ACCEPT_AUTO,
            invitation_mode=ConnRecord.INVITATION_MODE_MULTI,
            alias="Kitchen Sink Alias",
            their_public_did="did:sov:789",
            connection_protocol="didexchange/1.1",
        )
        await conn.save(session)
        conn_id = conn.connection_id

        # Add metadata
        await conn.metadata_set(session, "test_key", "test_value")

    # 2. V2 Read
    response = client.get(f"/connections/{conn_id}")
    assert response.status_code == 200, f"Error response: {response.text}"
    data = response.json()

    # 3. Assertions
    assert data["connectionId"] == conn_id
    assert data["alias"] == "Kitchen Sink Alias"
    assert data["state"] == "active"
    # Note: Legacy REQUESTER role maps to "invitee" string in DB
    assert data["theirRole"] == "invitee"
    assert data["invitationMode"] == "multi"
    assert data["accept"] == "auto"
    assert data["connectionProtocol"] == "didexchange/1.1"

    # 4. Metadata Read via V2
    meta_response = client.get(f"/connections/{conn_id}/metadata")
    assert meta_response.status_code == 200, f"Error response: {meta_response.text}"
    meta_data = meta_response.json()
    assert meta_data["results"]["test_key"] == "test_value"


@pytest.mark.asyncio
async def test_query_param_parity(profile, client):
    """Exhaustive Query Param Parity."""
    async with profile.session() as session:
        # Record 1: Active
        # Fixed: ACTIVE -> COMPLETED
        c1 = ConnRecord(state=ConnRecord.State.COMPLETED.rfc160, alias="alpha")
        await c1.save(session)
        # Record 2: Invitation
        c2 = ConnRecord(state=ConnRecord.State.INVITATION.rfc160, alias="beta")
        await c2.save(session)

    # Test State Filter
    resp_active = client.get("/connections", params={"state": "active"})
    assert resp_active.status_code == 200, f"Error response: {resp_active.text}"
    assert len(resp_active.json()["results"]) == 1
    assert resp_active.json()["results"][0]["alias"] == "alpha"

    resp_invitation = client.get("/connections", params={"state": "invitation"})
    assert len(resp_invitation.json()["results"]) == 1
    assert resp_invitation.json()["results"][0]["alias"] == "beta"

    # Test Alias Filter
    resp_alias = client.get("/connections", params={"alias": "alpha"})
    assert len(resp_alias.json()["results"]) == 1


@pytest.mark.asyncio
async def test_create_static_connection(profile, client):
    """Test static connection creation via V2."""
    valid_did = "2wJPyULfLLnYTEFYzByfUR"
    valid_their_did = "3Dn1SJNPaCXcvvJvSbsFWP"

    payload = {
        "my_did": f"did:sov:{valid_did}",
        "my_seed": "00000000000000000000000000000001",
        "their_did": f"did:sov:{valid_their_did}",
        "their_verkey": "3Dn1SJNPaCXcvvJvSbsFWP2xaCjMom3can8LtaK3adDT",
        "alias": "static-test",
    }

    response = client.post("/connections/create-static", json=payload)
    assert response.status_code == 200, f"Error response: {response.text}"
    data = response.json()

    assert data["myDid"] == payload["my_did"]
    assert "record" in data
    assert data["record"]["alias"] == "static-test"

    # Verify persistence
    async with profile.session() as session:
        found = await ConnRecord.retrieve_by_id(session, data["record"]["connectionId"])
        assert found.alias == "static-test"


@pytest.mark.asyncio
async def test_connection_list_parity(profile, client):
    """Test that connection list returns expected structure."""
    # 1. Seed data
    async with profile.session() as session:
        conn = ConnRecord(
            my_did="did:sov:123",
            their_did="did:sov:456",
            state=ConnRecord.State.COMPLETED.rfc160,
            alias="test-conn",
        )
        await conn.save(session)
        conn_id = conn.connection_id

    # 2. Query V2
    response = client.get("/connections")
    assert response.status_code == 200, f"Error response: {response.text}"
    data = response.json()

    assert "results" in data
    assert len(data["results"]) == 1
    record = data["results"][0]

    # 3. Check CamelCase conversion
    assert "connectionId" in record
    assert record["connectionId"] == conn_id
    assert "myDid" in record
    assert record["myDid"] == "did:sov:123"
    assert "state" in record
    assert record["state"] == "active"
