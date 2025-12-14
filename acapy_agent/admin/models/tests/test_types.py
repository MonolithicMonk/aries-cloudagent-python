"""Tests for centralized admin types."""

import pytest
from pydantic import BaseModel, ValidationError

from acapy_agent.admin.models.types import (
    DIDStr,
    EndpointStr,
    IndyDidStr,
    UUID4Str,
    VerkeyStr,
)


class TypeModel(BaseModel):
    """Test model for types."""

    uuid: UUID4Str
    did: DIDStr
    indy_did: IndyDidStr
    verkey: VerkeyStr
    endpoint: EndpointStr


def test_uuid4_validation():
    """Test UUID4Str validation."""
    valid_uuid = "3fa85f64-5717-4562-b3fc-2c963f66afa6"
    valid_indy_did = "WgWxqztrNooG92RXvxSTWv"  # 22 chars
    valid_verkey = "H3C2AVvLMv6gmMNam3uVAjZpfkcJCwDwnZn6z3wXmqPV"

    # Valid
    TypeModel.model_construct(uuid=valid_uuid)
    # We use explicit validation for construct
    TypeModel(
        uuid=valid_uuid,
        did="did:example:123",
        indy_did=valid_indy_did,
        verkey=valid_verkey,
    )

    # Invalid length
    with pytest.raises(ValidationError):
        TypeModel(
            uuid="short",
            did="did:example:123",
            indy_did=valid_indy_did,
            verkey=valid_verkey,
        )

    # Invalid characters
    with pytest.raises(ValidationError):
        TypeModel(
            uuid="3fa85f64-5717-4562-b3fc-2c963f66afaZ",  # Z is invalid hex
            did="did:example:123",
            indy_did=valid_indy_did,
            verkey=valid_verkey,
        )


def test_did_validation():
    """Test DIDStr validation."""
    valid_uuid = "3fa85f64-5717-4562-b3fc-2c963f66afa6"
    valid_indy_did = "WgWxqztrNooG92RXvxSTWv"
    valid_verkey = "H3C2AVvLMv6gmMNam3uVAjZpfkcJCwDwnZn6z3wXmqPV"

    valid_dids = [
        "did:sov:WRfXPg8dantKVubE3HX8pw",
        "did:key:z6MkpTHR8VNsBxYAAWHut2Geadd9jSwuBV8xRoAnwWsdvktH",
        "did:web:example.com",
    ]

    for did in valid_dids:
        # Just check the regex match logic in isolation or via model
        TypeModel(
            uuid=valid_uuid,
            did=did,
            indy_did=valid_indy_did,
            verkey=valid_verkey,
        )

    invalid_dids = [
        "nodid:start",
        "did:bad_char$",
        "did:empty:",
    ]

    for did in invalid_dids:
        with pytest.raises(ValidationError):
            TypeModel(
                uuid=valid_uuid,
                did=did,
                indy_did=valid_indy_did,
                verkey=valid_verkey,
            )


def test_verkey_validation():
    """Test VerkeyStr validation."""
    valid_uuid = "3fa85f64-5717-4562-b3fc-2c963f66afa6"
    valid_indy_did = "WgWxqztrNooG92RXvxSTWv"

    # Length check mostly
    valid_verkey = "H3C2AVvLMv6gmMNam3uVAjZpfkcJCwDwnZn6z3wXmqPV"  # 44 chars

    TypeModel(
        uuid=valid_uuid,
        did="did:example:123",
        indy_did=valid_indy_did,
        verkey=valid_verkey,
    )

    with pytest.raises(ValidationError):
        TypeModel(
            uuid=valid_uuid,
            did="did:example:123",
            indy_did=valid_indy_did,
            verkey="short",
        )


def test_endpoint_validation():
    """Test EndpointStr validation."""
    valid_uuid = "3fa85f64-5717-4562-b3fc-2c963f66afa6"
    valid_indy_did = "WgWxqztrNooG92RXvxSTWv"
    valid_verkey = "H3C2AVvLMv6gmMNam3uVAjZpfkcJCwDwnZn6z3wXmqPV"
    valid_did = "did:sov:WRfXPg8dantKVubE3HX8pw"

    valid_endpoints = [
        "http://localhost:8080",
        "https://example.com",
        "https://example.com/path/to/resource",
        "ws://example.com:8000",
        "wss://secure.example.com",
    ]

    for ep in valid_endpoints:
        TypeModel(
            uuid=valid_uuid,
            did=valid_did,
            indy_did=valid_indy_did,
            verkey=valid_verkey,
            endpoint=ep,
        )

    invalid_endpoints = [
        "not-a-url",
        "ftp://unsupported-scheme.com",
        "http:/missing-slash.com",
        "https://",  # Empty host
    ]

    for ep in invalid_endpoints:
        with pytest.raises(ValidationError):
            TypeModel(
                uuid=valid_uuid,
                did=valid_did,
                indy_did=valid_indy_did,
                verkey=valid_verkey,
                endpoint=ep,
            )
