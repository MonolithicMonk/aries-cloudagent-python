"""Centralized Pydantic types and validation patterns for Admin API v2.

These types correspond to the regex validation logic found in
acapy_agent/messaging/valid.py.
"""

from typing import Annotated
from pydantic import Field, StringConstraints

# Import the battle-tested validators from V1
from acapy_agent.messaging.valid import (
    ENDPOINT_VALIDATE,
    GENERIC_DID_VALIDATE,
    INDY_DID_VALIDATE,
    RAW_ED25519_2018_PUBLIC_KEY_VALIDATE,
    UUID4_VALIDATE,
)


def _get_pattern(validator):
    """Extract regex pattern string from Marshmallow Regexp validator."""
    if hasattr(validator, "regex"):
        return validator.regex.pattern
    return None


# --- Annotated Types ---

# We extract .regex from the Marshmallow validator to pass to Pydantic

UUID4Str = Annotated[
    str,
    StringConstraints(pattern=_get_pattern(UUID4_VALIDATE)),
    Field(
        description="UUID identifier",
        examples=["3fa85f64-5717-4562-b3fc-2c963f66afa6"],
        json_schema_extra={"format": "uuid"},
    ),
]

DIDStr = Annotated[
    str,
    StringConstraints(pattern=_get_pattern(GENERIC_DID_VALIDATE)),
    Field(
        description="Decentralized Identifier (DID)",
        examples=["did:sov:WRfXPg8dantKVubE3HX8pw"],
    ),
]

IndyDidStr = Annotated[
    str,
    StringConstraints(pattern=_get_pattern(INDY_DID_VALIDATE)),
    Field(description="Indy DID", examples=["WgWxqztrNooG92RXvxSTWv"]),
]

VerkeyStr = Annotated[
    str,
    StringConstraints(pattern=_get_pattern(RAW_ED25519_2018_PUBLIC_KEY_VALIDATE)),
    Field(
        description="Verification Key (Base58)",
        examples=["H3C2AVvLMv6gmMNam3uVAjZpfkcJCwDwnZn6z3wXmqPV"],
    ),
]


EndpointStr = Annotated[
    str,
    StringConstraints(pattern=_get_pattern(ENDPOINT_VALIDATE)),
    Field(
        description="URL endpoint",
        examples=["https://myhost:8021"],
    ),
]
