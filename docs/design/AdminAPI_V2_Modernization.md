# ACA-Py Admin API Modernization (V2)

## Overview
The ACA-Py Admin API is undergoing a major architectural modernization. We are transitioning from the legacy `aiohttp` + `marshmallow` stack to a modern, strictly typed **FastAPI** + **Pydantic V2** architecture.

**Primary Goals:**
1.  **Strict Contracts**: Guarantee that the code matches the OpenAPI specification.
2.  **Client Generation**: Enable reliable auto-generation of client SDKs (Java, .NET, TypeScript) via OpenAPI 3.1.
3.  **Modern Standards**: Adoption of industry-standard JSON conventions (camelCase) and rigorous validation.

## Architecture: The "Strangler Fig" Pattern
To ensure stability for existing deployments, the V2 API is deployed alongside the V1 API within the same process.

*   **V1 API (Legacy)**: Continues to run on the standard admin port (e.g., `8031`). **No changes** are made to existing logic.
*   **V2 API (Modern)**: Runs on a separate port (default: V1 port + 1, e.g., `8032`).
*   **Shared State**: Both APIs share the same `InjectionContext`, `Profile`, and `EventBus`.

This allows adopters to migrate client applications one endpoint at a time.

## Key Changes & Migration Guide

### 1. JSON Casing Strategy (Breaking Change for V2)
*   **V1 Behavior**: Uses `snake_case` for JSON fields (e.g., `thread_id`, `connection_id`).
*   **V2 Behavior**: Uses **`camelCase`** for JSON fields (e.g., `threadId`, `connectionId`).

**Reasoning**: `camelCase` is the de-facto standard for modern REST APIs and integrates more naturally with client-side languages like TypeScript, Java, and C#.

**Implementation**: All Pydantic models inherit from `BaseAdminModel` which automatically handles conversion:
```python
class PingResponse(BaseAdminModel):
    thread_id: str  # Python (Snake) -> JSON (Camel) "threadId"
```

### 2. Strict Validation
V2 endpoints reject extra fields by default and enforce strict type checking on inputs (e.g., UUIDs must be valid UUID strings, booleans must be actual booleans).

### 3. Authentication
V2 uses the standard `Authorization: Bearer <token>` or `X-API-KEY` headers via FastAPI's Dependency Injection system. The logic mirrors V1 but is implemented via `acapy_agent.admin.dependencies`.

## Patterns & Best Practices

### 1. Sending DIDComm Messages
FastAPI routes cannot directly access the internal `OutboundMessageRouter` in the same way `BaseHandler` classes do.
**Pattern**: Use a local or shared `FastAPIResponder` adapter that implements `BaseResponder`.
```python
class FastAPIResponder(BaseResponder):
    def __init__(self, profile, send_fn, **kwargs): ...
    async def send_outbound(self, message, **kwargs):
        return await self._send_fn(self._profile, message)
```
*Note: This class bridges the new API world with the legacy transport layer.*

### 2. Testing Strategy
*   **Tool**: `starlette.testclient.TestClient`.
*   **Scope**: Tests should be synchronous wrappers around the async API.
*   **Mocks**: Always mock `ConnRecord` (DB) and `outbound_message_router` (Transport).
*   **Verification**: Assert that the JSON response uses `camelCase` keys (e.g., `assert "threadId" in data`).

## Developer Guide: Porting a Protocol

To port a protocol (e.g., `basicmessage`) to V2:

1.  **Create V2 Package**: Create `acapy_agent/protocols/basicmessage/v1_0/v2/`.
2.  **Define Models**: Create `models.py`. Inherit from `BaseAdminModel`. Use Pydantic `Field` for descriptions.
3.  **Create Routes**: Create `routes.py`. Use `APIRouter`. Inject `Profile` via `Depends(get_profile)`.
4.  **Register Router**: Import and include the router in `acapy_agent/admin/fastapi_factory.py`.

## Roadmap
1.  **Foundation**: Infrastructure, Auth, and Pilot (TrustPing) [Complete]
2.  **Core Protocols**: Connections, Issue Credential, Present Proof [In Progress]
3.  **Standard Protocols**: DID Exchange, Basic Message, Discovery [Pending]
4.  **Advanced**: Revocation, Multitenancy [Pending]