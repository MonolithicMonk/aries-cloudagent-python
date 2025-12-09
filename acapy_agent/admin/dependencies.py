"""FastAPI dependencies for Admin API."""

from typing import Annotated

from fastapi import Depends, HTTPException, Request, Security
from fastapi.security import APIKeyHeader

from ..config.injection_context import InjectionContext
from ..core.profile import Profile
from ..utils import general as general_utils

# API Key Security Scheme
api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=False)


def get_context(request: Request) -> InjectionContext:
    """Retrieve the InjectionContext from the app state.

    This context is globally initialized when the AdminServer starts
    and attached to the FastAPI application state.
    """
    if not hasattr(request.app.state, "context"):
        raise HTTPException(
            status_code=500, detail="InjectionContext not initialized in app state."
        )
    return request.app.state.context


def get_profile(request: Request) -> Profile:
    """Retrieve the Root Profile from the app state."""
    if not hasattr(request.app.state, "root_profile"):
        raise HTTPException(
            status_code=500, detail="Root Profile not initialized in app state."
        )
    return request.app.state.root_profile


def get_settings(context: Annotated[InjectionContext, Depends(get_context)]) -> dict:
    """Retrieve settings from the context."""
    return context.settings


async def verify_admin_key(
    request: Request,
    api_key: str = Security(api_key_header),
    settings: dict = Depends(get_settings),
):
    """Verify the Admin API Key.

    This dependency ensures that the request is authorized.
    It checks against `admin.admin_api_key` in settings.
    It respects `admin.admin_insecure_mode`.
    It permits public endpoints (docs, health, root redirect).
    """
    # 1. Allow Public Endpoints
    # We strip trailing slashes to handle paths consistently
    path = request.url.path.rstrip("/")

    # Public paths allowed without auth
    public_paths = (
        "",  # Root redirect
        "/health",  # Liveness check
        "/api/doc",  # Swagger UI HTML
        "/api/docs/swagger.json",  # OpenAPI Spec JSON
        "/favicon.ico",  # Browser icon
    )

    if path in public_paths or path.startswith("/api/doc/"):
        return

    # 2. Allow OPTIONS (CORS Pre-flight)
    if request.method == "OPTIONS":
        return

    # 3. Check Configuration
    admin_api_key = settings.get("admin.admin_api_key")
    insecure_mode = settings.get("admin.admin_insecure_mode", False)

    if insecure_mode:
        return

    # 4. Verify Key
    if not admin_api_key:
        raise HTTPException(status_code=500, detail="Server misconfiguration: no API key")

    if not general_utils.const_compare(admin_api_key, api_key):
        raise HTTPException(
            status_code=401, detail="Unauthorized: API Key invalid or missing"
        )
