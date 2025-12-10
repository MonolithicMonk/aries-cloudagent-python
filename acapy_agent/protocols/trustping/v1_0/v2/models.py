"""Pydantic models for TrustPing v1.0 Admin API v2."""

from typing import Optional

from pydantic import Field

from acapy_agent.admin.models.base import BaseAdminModel


class PingRequest(BaseAdminModel):
    """Request model for sending a trust ping."""

    comment: Optional[str] = Field(None, description="Comment for the ping message")


class PingResponse(BaseAdminModel):
    """Response model for a sent trust ping."""

    thread_id: Optional[str] = Field(None, description="Thread ID of the ping message")
