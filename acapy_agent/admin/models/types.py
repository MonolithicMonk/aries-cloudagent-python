"""Centralized Pydantic types and validation patterns for Admin API v2.

These types correspond to the regex validation logic found in
acapy_agent/messaging/valid.py.
"""

from typing import Annotated

from pydantic import Field, StringConstraints

# --- Regex Patterns ---
# Matches UUIDv4
UUID4_PATTERN = r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-4[0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$"

# Matches generic DIDs (did:method:identifier)
# Based on W3C DID Core specification
DID_PATTERN = r"^did:[a-z0-9]+:[a-zA-Z0-9._%-]*:?[a-zA-Z0-9._%-]+$"

# Matches Indy DIDs (base58, 21-22 chars, optional did:sov: prefix)
INDY_DID_PATTERN = r"^(did:sov:)?[1-9A-HJ-NP-Za-km-z]{21,22}$"

# Matches Verkeys (Base58, ~43-44 chars, but we allow 40-50 for safety)
VERKEY_PATTERN = r"^[1-9A-HJ-NP-Za-km-z]{40,50}$"


# --- Annotated Types ---

UUID4Str = Annotated[
    str,
    StringConstraints(pattern=UUID4_PATTERN, min_length=36, max_length=36),
    Field(
        description="UUID identifier",
        examples=["3fa85f64-5717-4562-b3fc-2c963f66afa6"],
    ),
]

DIDStr = Annotated[
    str,
    StringConstraints(pattern=DID_PATTERN),
    Field(
        description="Decentralized Identifier (DID)",
        examples=["did:sov:WRfXPg8dantKVubE3HX8pw"],
    ),
]

IndyDidStr = Annotated[
    str,
    StringConstraints(pattern=INDY_DID_PATTERN),
    Field(
        description="Indy DID",
        examples=["WgWxqztrNooG92RXvxSTWv"],
    ),
]

VerkeyStr = Annotated[
    str,
    StringConstraints(pattern=VERKEY_PATTERN),
    Field(
        description="Verification Key (Base58)",
        examples=["H3C2AVvLMv6gmMNam3uVAjZpfkcJCwDwnZn6z3wXmqPV"],
    ),
]
