"""FastAPI Application Factory for Admin API v2."""

import logging
from typing import Callable, Coroutine

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import RedirectResponse

from ..config.injection_context import InjectionContext
from ..core.profile import Profile
from .dependencies import verify_admin_key

# Import Protocol Routers
from ..protocols.trustping.v1_0.v2.routes import router as trustping_router

LOGGER = logging.getLogger(__name__)


def create_admin_app(
    context: InjectionContext,
    root_profile: Profile,
    outbound_message_router: Callable[..., Coroutine],
) -> FastAPI:
    """Create and configure the FastAPI application for Admin API v2.

    Args:
        context: The global injection context.
        root_profile: The root profile of the agent.
        outbound_message_router: Coroutine for delivering outbound messages.

    Returns:
        FastAPI: The configured application instance.
    """
    settings = context.settings
    title = settings.get("default_label", "Aries Cloud Agent")
    description = "ACA-Py Admin API v2"

    # Initialize FastAPI with legacy-compatible paths
    app = FastAPI(
        title=f"{title} (v2)",
        description=description,
        version="2.0.0",
        docs_url="/api/doc",  # Match legacy Swagger UI path
        redoc_url=None,  # Legacy does not expose ReDoc
        openapi_url="/api/docs/swagger.json",  # Match legacy OpenAPI spec path
        dependencies=[
            # Apply global authentication dependency
            # This ensures all endpoints require the API Key unless explicitly overridden
        ],
    )

    # Store context and profile in app state for dependencies to access
    app.state.context = context
    app.state.root_profile = root_profile
    app.state.outbound_message_router = outbound_message_router

    # Add CORS Middleware
    # Matches aiohttp behavior: allow all origins/methods/headers for Admin API
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add Security Dependency globally
    app.router.dependencies.append(Depends(verify_admin_key))

    # --- Root Redirect ---
    @app.get("/", include_in_schema=False)
    async def redirect_root():
        """Redirect root to legacy docs path."""

        return RedirectResponse(url="/api/doc")

    @app.get("/health", tags=["server"])
    async def health_check():
        """Liveliness check."""
        return {"status": "ok"}

    # --- Register Protocol Routers ---
    app.include_router(trustping_router)

    LOGGER.info("FastAPI Admin V2 Application initialized")
    return app
