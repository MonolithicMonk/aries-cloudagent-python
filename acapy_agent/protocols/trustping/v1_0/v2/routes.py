"""FastAPI routes for TrustPing v1.0."""

import logging
import warnings
from typing import Callable
from weakref import ref

from fastapi import APIRouter, Depends, HTTPException, Path, Request

from acapy_agent.admin.dependencies import get_profile
from acapy_agent.connections.models.conn_record import ConnRecord
from acapy_agent.core.profile import Profile
from acapy_agent.messaging.responder import BaseResponder
from acapy_agent.protocols.trustping.v1_0.messages.ping import Ping
from acapy_agent.storage.error import StorageNotFoundError
from acapy_agent.transport.outbound.message import OutboundMessage
from acapy_agent.transport.outbound.status import OutboundSendStatus

from .models import PingRequest, PingResponse

LOGGER = logging.getLogger(__name__)

router = APIRouter()


class FastAPIResponder(BaseResponder):
    """Responder implementation for FastAPI Admin API."""

    def __init__(self, profile: Profile, send_fn: Callable, **kwargs):
        """Initialize the responder."""
        super().__init__(**kwargs)
        self._profile = ref(profile)
        self._send_fn = send_fn

    async def send_outbound(
        self, message: OutboundMessage, **kwargs
    ) -> OutboundSendStatus:
        """Send outbound message via the provided send function."""
        profile = self._profile()
        if not profile:
            raise RuntimeError("Profile weakref expired")
        return await self._send_fn(profile, message)

    async def send_webhook(self, topic: str, payload: dict):
        """Dispatch a webhook.

        DEPRECATED: use the event bus instead.
        """
        warnings.warn(
            "responder.send_webhook is deprecated; please use the event bus instead.",
            DeprecationWarning,
        )
        profile = self._profile()
        if not profile:
            raise RuntimeError("Profile weakref expired")
        await profile.notify(f"acapy::webhook::{topic}", payload)


@router.post(
    "/connections/{conn_id}/send-ping",
    response_model=PingResponse,
    summary="Send a trust ping to a connection",
    tags=["trustping"],
)
async def send_ping(
    request: Request,
    conn_id: str = Path(..., description="Connection identifier"),
    body: PingRequest = None,
    profile: Profile = Depends(get_profile),
):
    """Send a trust ping to a connection.
    
    This endpoint sends a Trust Ping message to the specified connection to check
    if it is active and responsive.
    
    **Note:** This relies on the Trust Ping Protocol 1.0.
    """
    body = body or PingRequest()

    # Check connection existence and state
    try:
        async with profile.session() as session:
            connection = await ConnRecord.retrieve_by_id(session, conn_id)
    except StorageNotFoundError:
        raise HTTPException(status_code=404, detail="Connection not found")

    if not connection.is_ready:
        raise HTTPException(status_code=400, detail=f"Connection {conn_id} not ready")

    # Prepare message
    msg = Ping(comment=body.comment)

    # Get outbound router from app state
    if not hasattr(request.app.state, "outbound_message_router"):
        raise HTTPException(
            status_code=500, detail="Outbound message router not initialized"
        )
    outbound_router = request.app.state.outbound_message_router

    # Send message
    responder = FastAPIResponder(profile, outbound_router)
    await responder.send(msg, connection_id=conn_id)

    return PingResponse(thread_id=msg._thread_id)