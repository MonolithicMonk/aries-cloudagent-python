"""Base Pydantic models for Admin API v2."""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

# Import centralized types
# Re-exporting for backward compatibility within the admin module
from .types import DIDStr  # noqa: F401
from .types import UUID4Str as ConnectionIdStr  # noqa: F401
from .types import UUID4Str as ThreadIdStr  # noqa: F401
from .types import VerkeyStr  # noqa: F401


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
