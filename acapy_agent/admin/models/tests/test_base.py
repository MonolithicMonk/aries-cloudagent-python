"""Tests for BaseAdminModel and common types."""

import pytest
from pydantic import ValidationError

from ..base import BaseAdminModel, ConnectionIdStr, DIDStr, VerkeyStr


class ExampleModel(BaseAdminModel):
    """Test model."""

    test_field: str
    did_field: DIDStr = "did:sov:WRfXPg8dantKVubE3HX8pw"


def test_alias_generator():
    """Test that snake_case fields are converted to camelCase in JSON."""
    model = ExampleModel(test_field="value")

    # Test serialization (python -> json)
    dump = model.model_dump(by_alias=True)
    assert "testField" in dump
    assert dump["testField"] == "value"

    # Ensure raw python access remains snake_case
    assert model.test_field == "value"


def test_population_by_name():
    """Test that we can instantiate models using either snake_case or camelCase."""
    # By snake_case (internal use)
    model_snake = ExampleModel(test_field="val1")
    assert model_snake.test_field == "val1"

    # By camelCase (API input)
    model_camel = ExampleModel.model_validate({"testField": "val2"})
    assert model_camel.test_field == "val2"


def test_did_validation():
    """Test DID string validation."""

    class DidModel(BaseAdminModel):
        did: DIDStr

    # Valid SOV DID
    DidModel(did="did:sov:WRfXPg8dantKVubE3HX8pw")
    # Valid Peer DID
    DidModel(did="did:peer:2.Ez6Lqp...")
    # Valid Key DID
    DidModel(did="did:key:z6MkhaXgBZDvotDkL5257faiztiGiC2QtKLGpbnnEGta2doK")

    # Invalid (bad prefix)
    with pytest.raises(ValidationError):
        DidModel(did="bad:sov:WRfXPg8dantKVubE3HX8pw")

    # Invalid (spaces)
    with pytest.raises(ValidationError):
        DidModel(did="did: sov:WRfXPg8dantKVubE3HX8pw")


def test_verkey_validation():
    """Test Verkey string validation."""

    class VerkeyModel(BaseAdminModel):
        vk: VerkeyStr

    # Valid
    VerkeyModel(vk="H3C2AVvLMv6gmMNam3uVAjZpfkcJCwDwnZn6z3wXmqPV")

    # Invalid (too short)
    with pytest.raises(ValidationError):
        VerkeyModel(vk="short")


def test_connection_id_validation():
    """Test Connection ID (UUID) validation."""

    class ConnModel(BaseAdminModel):
        conn_id: ConnectionIdStr

    # Valid UUID
    ConnModel(conn_id="3fa85f64-5717-4562-b3fc-2c963f66afa6")

    # Invalid (not uuid)
    with pytest.raises(ValidationError):
        ConnModel(conn_id="not-a-uuid")
