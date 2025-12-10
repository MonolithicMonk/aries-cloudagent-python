"""Pydantic models for Connection Records (V2)."""

from enum import Enum
from typing import Optional

from pydantic import Field, ConfigDict

from acapy_agent.admin.models.base import BaseRecordModel
from acapy_agent.admin.models.types import UUID4Str, DIDStr, VerkeyStr


class ConnRecordState(str, Enum):
    """Connection record states."""

    INIT = "init"
    INVITATION = "invitation"
    REQUEST = "request"
    RESPONSE = "response"
    ACTIVE = "active"
    COMPLETED = "completed"
    ABANDONED = "abandoned"
    ERROR = "error"


class ConnRecordRole(str, Enum):
    """Connection record roles."""

    REQUESTER = "requester"
    RESPONDER = "responder"
    INVITER = "inviter"
    INVITEE = "invitee"


class ConnRecordAccept(str, Enum):
    """Connection acceptance modes."""

    MANUAL = "manual"
    AUTO = "auto"


class ConnRecordInvitationMode(str, Enum):
    """Connection invitation modes."""

    ONCE = "once"
    MULTI = "multi"
    STATIC = "static"


class ConnRecordSchema(BaseRecordModel):
    """Connection Record Schema for V2 Admin API.

    Maps to acapy_agent.connections.models.conn_record.ConnRecord
    """

    connection_id: UUID4Str = Field(..., description="Connection identifier")

    my_did: Optional[DIDStr] = Field(None, description="Our DID for connection")

    their_did: Optional[DIDStr] = Field(None, description="Their DID for connection")

    their_label: Optional[str] = Field(
        None, description="Their label for connection", examples=["Bob"]
    )

    their_role: Optional[ConnRecordRole] = Field(
        None, description="Their role in the connection protocol"
    )

    connection_protocol: Optional[str] = Field(
        None, description="Connection protocol used", examples=["didexchange/1.1"]
    )

    rfc23_state: Optional[str] = Field(
        None, description="State per RFC 23", examples=["invitation-sent"]
    )

    inbound_connection_id: Optional[UUID4Str] = Field(
        None, description="Inbound routing connection id to use"
    )

    invitation_key: Optional[VerkeyStr] = Field(
        None, description="Public key for connection"
    )

    invitation_msg_id: Optional[UUID4Str] = Field(
        None, description="ID of out-of-band invitation message"
    )

    request_id: Optional[UUID4Str] = Field(
        None, description="Connection request identifier"
    )

    state: Optional[ConnRecordState] = Field(None, description="Connection state")

    accept: Optional[ConnRecordAccept] = Field(
        None, description="Connection acceptance: manual or auto"
    )

    error_msg: Optional[str] = Field(None, description="Error message")

    invitation_mode: Optional[ConnRecordInvitationMode] = Field(
        None, description="Invitation mode"
    )

    alias: Optional[str] = Field(
        None,
        description="Optional alias to apply to connection for later use",
        examples=["Bob, providing quotes"],
    )

    their_public_did: Optional[DIDStr] = Field(
        None, description="Other agent's public DID for connection"
    )

    # Configuration to ensure Enum values are used during serialization
    model_config = ConfigDict(use_enum_values=True)
