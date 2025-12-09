"""Base Pydantic models for Admin API v2."""

from typing import Annotated, Optional

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class BaseAdminModel(BaseModel):
    """Base model for all Admin API schemas.

    Configures automatic CamelCase aliasing for JSON serialization/deserialization
    while keeping Python attributes in snake_case.
    """

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        # Pydantic V2 strict mode is powerful but can be brittle for legacy data.
        # We start with strict=False (default) but explicit types.
        from_attributes=True,  # Allows creating from ORM/Attribute objects
    )


# --- Common Field Types ---

# Standard DID Validator (Generic)
# Matches: did:method:specific-id
DIDStr = Annotated[
    str,
    Field(
        pattern=r"^did:[a-z0-9]+:[a-zA-Z0-9._%-]*:?[a-zA-Z0-9._%-]+$",
        examples=["did:sov:WRfXPg8dantKVubE3HX8pw"],
    ),
]

# Verkey / Multikey
# Base58 check (roughly)
VerkeyStr = Annotated[
    str,
    Field(
        min_length=40,
        max_length=50,
        examples=["H3C2AVvLMv6gmMNam3uVAjZpfkcJCwDwnZn6z3wXmqPV"],
    ),
]

# UUID4
ConnectionIdStr = Annotated[
    str,
    Field(
        min_length=36,
        max_length=36,
        pattern=r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-4[0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$",
        examples=["3fa85f64-5717-4562-b3fc-2c963f66afa6"],
        description="Connection identifier",
    ),
]

ThreadIdStr = Annotated[
    str,
    Field(examples=["3fa85f64-5717-4562-b3fc-2c963f66afa6"], description="Thread ID"),
]


class BaseRecordModel(BaseAdminModel):
    """Base model representing a stored record (like ConnectionRecord)."""

    created_at: Optional[str] = Field(
        None, description="Time of record creation in ISO8601 format"
    )
    updated_at: Optional[str] = Field(
        None, description="Time of last record update in ISO8601 format"
    )
    # We allow extra fields to pass through for now to support plugin extensions
    # that might tack data onto standard records.
    model_config = ConfigDict(extra="ignore")
