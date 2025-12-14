"""FastAPI routes for Connections (V2)."""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query

from acapy_agent.admin.dependencies import get_context, get_profile
from acapy_agent.config.injection_context import InjectionContext
from acapy_agent.connections.base_manager import BaseConnectionManager
from acapy_agent.connections.models.conn_record import ConnRecord
from acapy_agent.core.profile import Profile
from acapy_agent.storage.error import StorageNotFoundError

from .models import (
    ConnectionListSchema,
    ConnectionMetadataSchema,
    ConnectionMetadataSetRequestSchema,
    ConnectionModuleResponseSchema,
    ConnectionProtocol,
    ConnectionStaticRequestSchema,
    ConnectionStaticResultSchema,
    ConnRecordRole,
    ConnRecordSchema,
    ConnRecordState,
    EndpointsResultSchema,
    OrderBy,
)

LOGGER = logging.getLogger(__name__)

router = APIRouter(prefix="/connections", tags=["connection"])


@router.get(
    "",
    response_model=ConnectionListSchema,
    summary="Query agent-to-agent connections",
)
async def get_connections(
    alias: Optional[str] = Query(None, description="Alias"),
    connection_protocol: Optional[ConnectionProtocol] = Query(
        None, description="Connection protocol used", examples=["didexchange/1.1"]
    ),
    descending: bool = Query(
        False, description="Order results in descending order if true"
    ),
    invitation_key: Optional[str] = Query(None, description="Invitation key"),
    invitation_msg_id: Optional[str] = Query(
        None, description="Invitation message identifier"
    ),
    limit: int = Query(100, ge=1, description="Number of results to return"),
    my_did: Optional[str] = Query(None, description="My DID"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    order_by: Optional[OrderBy] = Query(
        OrderBy.ID, description="Column to order by. Only 'id' is currently supported."
    ),
    state: Optional[ConnRecordState] = Query(None, description="Connection state"),
    their_did: Optional[str] = Query(None, description="Their DID"),
    their_public_did: Optional[str] = Query(None, description="Their Public DID"),
    their_role: Optional[ConnRecordRole] = Query(
        None, description="Their role in the connection protocol"
    ),
    profile: Profile = Depends(get_profile),
):
    """Query connection records."""
    tag_filter = {}
    if my_did:
        tag_filter["my_did"] = my_did
    if their_did:
        tag_filter["their_did"] = their_did
    if invitation_key:
        tag_filter["invitation_key"] = invitation_key
    if their_public_did:
        tag_filter["their_public_did"] = their_public_did
    if invitation_msg_id:
        tag_filter["invitation_msg_id"] = invitation_msg_id

    post_filter = {}
    if alias:
        post_filter["alias"] = alias
    if state:
        # Convert Enum to string required by ConnRecord.State
        post_filter["state"] = list(ConnRecord.State.get(state.value).value)
    if their_role:
        post_filter["their_role"] = list(ConnRecord.Role.get(their_role.value).value)
    if connection_protocol:
        post_filter["connection_protocol"] = connection_protocol.value

    async with profile.session() as session:
        records = await ConnRecord.query(
            session,
            tag_filter,
            limit=limit,
            offset=offset,
            order_by=order_by.value if order_by else "id",
            descending=descending,
            post_filter_positive=post_filter,
            alt=True,
        )

    # Pydantic validation via from_attributes=True
    return ConnectionListSchema(results=[ConnRecordSchema.model_validate(r) for r in records])


@router.get(
    "/{conn_id}",
    response_model=ConnRecordSchema,
    summary="Fetch a single connection record",
)
async def get_connection(
    conn_id: str = Path(..., description="Connection identifier"),
    profile: Profile = Depends(get_profile),
):
    """Fetch a single connection record."""
    try:
        async with profile.session() as session:
            record = await ConnRecord.retrieve_by_id(session, conn_id)
        return ConnRecordSchema.model_validate(record)
    except StorageNotFoundError:
        raise HTTPException(status_code=404, detail="Connection not found")


@router.delete(
    "/{conn_id}",
    summary="Remove an existing connection record",
    status_code=200,
    response_model=ConnectionModuleResponseSchema,
)
async def delete_connection(
    conn_id: str = Path(..., description="Connection identifier"),
    profile: Profile = Depends(get_profile),
):
    """Remove a connection record."""
    try:
        async with profile.session() as session:
            connection = await ConnRecord.retrieve_by_id(session, conn_id)
            await connection.delete_record(session)
    except StorageNotFoundError:
        raise HTTPException(status_code=404, detail="Connection not found")

    return {}


@router.post(
    "/create-static",
    response_model=ConnectionStaticResultSchema,
    summary="Create a new static connection",
)
async def create_static_connection(
    body: ConnectionStaticRequestSchema,
    context: InjectionContext = Depends(get_context),
    profile: Profile = Depends(get_profile),
):
    """Create a new static connection."""
    connection_mgr = BaseConnectionManager(profile)
    try:
        (
            my_info,
            their_info,
            connection,
        ) = await connection_mgr.create_static_connection(
            my_seed=body.my_seed,
            my_did=body.my_did,
            their_seed=body.their_seed,
            their_did=body.their_did,
            their_verkey=body.their_verkey,
            their_endpoint=body.their_endpoint,
            their_label=body.their_label,
            alias=body.alias,
        )
    except Exception as e:
        LOGGER.exception("Error creating static connection")
        raise HTTPException(status_code=400, detail=str(e))

    return ConnectionStaticResultSchema(
        my_did=my_info.did,
        my_verkey=my_info.verkey,
        my_endpoint=context.settings.get("default_endpoint") or "",
        their_did=their_info.did,
        their_verkey=their_info.verkey,
        record=ConnRecordSchema.model_validate(connection),
    )


@router.get(
    "/{conn_id}/endpoints",
    response_model=EndpointsResultSchema,
    summary="Fetch connection remote endpoint",
)
async def get_endpoints(
    conn_id: str = Path(..., description="Connection identifier"),
    context: InjectionContext = Depends(get_context),
    profile: Profile = Depends(get_profile),
):
    """Fetch connection endpoints."""
    connection_mgr = BaseConnectionManager(profile)
    try:
        endpoints = await connection_mgr.get_endpoints(conn_id)
    except StorageNotFoundError:
        raise HTTPException(status_code=404, detail="Connection not found")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    return EndpointsResultSchema(my_endpoint=endpoints[0], their_endpoint=endpoints[1])


@router.get(
    "/{conn_id}/metadata",
    response_model=ConnectionMetadataSchema,
    summary="Fetch connection metadata",
)
async def get_metadata(
    conn_id: str = Path(..., description="Connection identifier"),
    key: Optional[str] = Query(None, description="Key to retrieve"),
    profile: Profile = Depends(get_profile),
):
    """Fetch connection metadata."""
    try:
        async with profile.session() as session:
            record = await ConnRecord.retrieve_by_id(session, conn_id)
            if key:
                result = await record.metadata_get(session, key)
                # Wrap single result in dict to match schema
                result = {key: result} if result is not None else {}
            else:
                result = await record.metadata_get_all(session)
    except StorageNotFoundError:
        raise HTTPException(status_code=404, detail="Connection not found")

    return ConnectionMetadataSchema(results=result)


@router.post(
    "/{conn_id}/metadata",
    response_model=ConnectionMetadataSchema,
    summary="Set connection metadata",
)
async def set_metadata(
    body: ConnectionMetadataSetRequestSchema,
    conn_id: str = Path(..., description="Connection identifier"),
    profile: Profile = Depends(get_profile),
):
    """Set connection metadata."""
    try:
        async with profile.session() as session:
            record = await ConnRecord.retrieve_by_id(session, conn_id)
            for key, value in body.metadata.items():
                await record.metadata_set(session, key, value)
            result = await record.metadata_get_all(session)
    except StorageNotFoundError:
        raise HTTPException(status_code=404, detail="Connection not found")

    return ConnectionMetadataSchema(results=result)
