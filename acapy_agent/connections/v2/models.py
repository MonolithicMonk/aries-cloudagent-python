"""Pydantic models for Connection Records (V2)."""

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import ConfigDict, Field
from pydantic.alias_generators import to_camel

from acapy_agent.admin.models.base import BaseAdminModel, BaseRecordModel
from acapy_agent.admin.models.types import DIDStr, IndyDidStr, UUID4Str, VerkeyStr


class ConnRecordState(str, Enum):
    """Connection record states."""

    ABANDONED = "abandoned"
    ACTIVE = "active"
    COMPLETED = "completed"
    ERROR = "error"
    INIT = "init"
    INVITATION = "invitation"
    REQUEST = "request"
    RESPONSE = "response"
    START = "start"  # Legacy compatibility


class ConnRecordRole(str, Enum):
    """Connection record roles."""

    INVITEE = "invitee"
    INVITER = "inviter"
    REQUESTER = "requester"
    RESPONDER = "responder"


class ConnRecordAccept(str, Enum):
    """Connection acceptance modes."""

    AUTO = "auto"
    MANUAL = "manual"


class ConnRecordInvitationMode(str, Enum):
    """Connection invitation modes."""

    MULTI = "multi"
    ONCE = "once"
    STATIC = "static"


class ConnectionProtocol(str, Enum):
    """Connection protocols."""

    DIDEXCHANGE_1_0 = "didexchange/1.0"
    DIDEXCHANGE_1_1 = "didexchange/1.1"


class OrderBy(str, Enum):
    """Order by options."""

    ID = "id"


class ConnRecordSchema(BaseRecordModel):
    """Connection Record Schema for V2 Admin API.

    Maps to acapy_agent.connections.models.conn_record.ConnRecord
    """

    accept: Optional[ConnRecordAccept] = Field(
        None,
        description="Connection acceptance: manual or auto",
        examples=["auto"],
    )

    alias: Optional[str] = Field(
        None,
        description="Optional alias to apply to connection for later use",
        examples=["Bob, providing quotes"],
    )

    connection_id: UUID4Str = Field(
        ...,
        description="Connection identifier",
        examples=["3fa85f64-5717-4562-b3fc-2c963f66afa6"],
    )

    connection_protocol: Optional[ConnectionProtocol] = Field(
        None, description="Connection protocol used", examples=["didexchange/1.1"]
    )

    created_at: Optional[str] = Field(
        None,
        description="Time of record creation in ISO8601 format",
        pattern=r"^\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(\.\d{1,6})?([+-]\d{2}:?\d{2}|Z)?$",
        examples=["2021-12-31T23:59:59Z"],
    )

    error_msg: Optional[str] = Field(
        None,
        description="Error message",
        examples=["No DIDDoc provided; cannot connect to public DID"],
    )

    inbound_connection_id: Optional[UUID4Str] = Field(
        None,
        description="Inbound routing connection id to use",
        examples=["3fa85f64-5717-4562-b3fc-2c963f66afa6"],
    )

    invitation_key: Optional[VerkeyStr] = Field(
        None,
        description="Public key for connection",
        examples=["H3C2AVvLMv6gmMNam3uVAjZpfkcJCwDwnZn6z3wXmqPV"],
    )

    invitation_mode: Optional[ConnRecordInvitationMode] = Field(
        None, description="Invitation mode", examples=["once"]
    )

    invitation_msg_id: Optional[UUID4Str] = Field(
        None,
        description="ID of out-of-band invitation message",
        examples=["3fa85f64-5717-4562-b3fc-2c963f66afa6"],
    )

    my_did: Optional[DIDStr] = Field(None, description="Our DID for connection")

    request_id: Optional[UUID4Str] = Field(
        None,
        description="Connection request identifier",
        examples=["3fa85f64-5717-4562-b3fc-2c963f66afa6"],
    )

    rfc23_state: Optional[str] = Field(
        None,
        description="State per RFC 23",
        examples=["invitation-sent"],
        json_schema_extra={"readOnly": True},
    )

    state: Optional[ConnRecordState] = Field(
        None, description="Connection state", examples=["active"]
    )

    their_did: Optional[DIDStr] = Field(
        None,
        description="Their DID for connection",
        examples=["WgWxqztrNooG92RXvxSTWv"],
    )

    their_label: Optional[str] = Field(
        None, description="Their label for connection", examples=["Bob"]
    )

    their_public_did: Optional[DIDStr] = Field(
        None,
        description="Other agent's public DID for connection",
        examples=["WgWxqztrNooG92RXvxSTWv"],
    )

    their_role: Optional[ConnRecordRole] = Field(
        None, description="Their role in the connection protocol", examples=["requester"]
    )

    updated_at: Optional[str] = Field(
        None,
        description="Time of last record update in ISO8601 format",
        pattern=r"^\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(\.\d{1,6})?([+-]\d{2}:?\d{2}|Z)?$",
        examples=["2021-12-31T23:59:59Z"],
    )

    # Configuration must include base settings + enum serialization
    model_config = ConfigDict(
        # title="ConnRecord",
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
        use_enum_values=True,
    )


# HACK: Force the OpenAPI Component name to be 'ConnRecord' instead of 'ConnRecordSchema'
# This satisfies parity with the legacy API while keeping the class name consistent.
ConnRecordSchema.__name__ = "ConnRecord"


class ConnectionListSchema(BaseAdminModel):
    """Response model for a list of connections."""

    results: List[ConnRecordSchema]

    # model_config = ConfigDict(title="ConnectionList")

ConnectionListSchema.__name__ = "ConnectionList"


class ConnectionStaticRequestSchema(BaseAdminModel):
    """Request model for creating a static connection."""

    alias: Optional[str] = Field(
        None,
        description="Alias to assign to this connection",
        examples=["Bob, providing quotes"],
    )
    my_did: Optional[IndyDidStr] = Field(
        None, description="Local DID", examples=["WgWxqztrNooG92RXvxSTWv"]
    )
    my_seed: Optional[str] = Field(
        None,
        description="Seed to use for the local DID",
        examples=["00000000000000000000000000000001"],
    )
    their_did: Optional[IndyDidStr] = Field(
        None, description="Remote DID", examples=["WgWxqztrNooG92RXvxSTWv"]
    )
    their_endpoint: Optional[str] = Field(
        None, description="URL endpoint for other party", examples=["https://myhost:8021"]
    )
    their_label: Optional[str] = Field(
        None, description="Other party's label for this connection", examples=["Bob"]
    )
    their_seed: Optional[str] = Field(
        None,
        description="Seed to use for the remote DID",
        examples=["00000000000000000000000000000001"],
    )
    their_verkey: Optional[VerkeyStr] = Field(
        None,
        description="Remote verification key",
        examples=["H3C2AVvLMv6gmMNam3uVAjZpfkcJCwDwnZn6z3wXmqPV"],
    )

    model_config = ConfigDict(
        # title="ConnectionStaticRequest",
        alias_generator=to_camel,
        populate_by_name=True,
    )


ConnectionStaticRequestSchema.__name__ = "ConnectionStaticRequest"


class ConnectionStaticResultSchema(BaseAdminModel):
    """Response model for a static connection creation."""

    my_did: str = Field(..., description="Local DID", examples=["WgWxqztrNooG92RXvxSTWv"])
    my_endpoint: str = Field(
        ..., description="My URL endpoint", examples=["https://myhost:8021"]
    )
    my_verkey: str = Field(
        ...,
        description="My verification key",
        examples=["H3C2AVvLMv6gmMNam3uVAjZpfkcJCwDwnZn6z3wXmqPV"],
    )
    record: ConnRecordSchema = Field(
        ...,
        description="Created connection record",
        example=ConnectionListSchema.model_json_schema(),
    )
    their_did: str = Field(
        ..., description="Remote DID", examples=["WgWxqztrNooG92RXvxSTWv"]
    )
    their_verkey: str = Field(
        ...,
        description="Remote verification key",
        examples=["H3C2AVvLMv6gmMNam3uVAjZpfkcJCwDwnZn6z3wXmqPV"],
    )

    model_config = ConfigDict(
        # title="ConnectionStaticResult",
        alias_generator=to_camel,
        populate_by_name=True,
    )


ConnectionStaticResultSchema.__name__ = "ConnectionStaticResult"


class ConnectionMetadataSchema(BaseAdminModel):
    """Response model for connection metadata."""

    results: Dict[str, Any] = Field(
        ...,
        description="Dictionary of metadata associated with connection.",
        examples=[{"key": "value"}],
    )

    # model_config = ConfigDict(title="ConnectionMetadata")


ConnectionMetadataSchema.__name__ = "ConnectionMetadata"


class ConnectionMetadataSetRequestSchema(BaseAdminModel):
    """Request model for setting connection metadata."""

    metadata: Dict[str, Any] = Field(
        ...,
        description="Dictionary of metadata to set for connection.",
        examples=[{"setting_a": "value_a", "setting_b": "value_b"}],
    )

    model_config = ConfigDict(
        # title="ConnectionMetadataSetRequest",
        alias_generator=to_camel,
        populate_by_name=True,
    )


ConnectionMetadataSetRequestSchema.__name__ = "ConnectionMetadataSetRequest"


class EndpointsResultSchema(BaseAdminModel):
    """Response model for connection endpoints."""

    my_endpoint: Optional[str] = Field(
        None,
        description="My endpoint",
        examples=["https://myhost:8021"],
    )
    their_endpoint: Optional[str] = Field(
        None,
        description="Their endpoint",
        examples=["https://theirhost:8021"],
    )

    # model_config = ConfigDict(title="EndpointsResult")


EndpointsResultSchema.__name__ = "EndpointsResult"


class ConnectionModuleResponseSchema(BaseAdminModel):
    """Response model for connection module (Empty object)."""

    model_config = ConfigDict(
        # title="ConnectionModuleResponse", # Replaced by __name__ override
        alias_generator=to_camel,
        populate_by_name=True,
    )


# Override name for OpenAPI parity
ConnectionModuleResponseSchema.__name__ = "ConnectionModuleResponse"
