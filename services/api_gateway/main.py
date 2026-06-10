from __future__ import annotations

import os

import httpx
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from shared.auth import AuthPrincipal, principal_from_authorization
from shared.logging import configure_logging, install_api_logging
from shared.tenancy import DEFAULT_STORE_ID

SERVICE_ROUTES = {
    "identity": os.getenv("IDENTITY_SERVICE_URL", "http://localhost:8008"),
    "catalog": os.getenv("CATALOG_SERVICE_URL", "http://localhost:8001"),
    "orders": os.getenv("ORDER_SERVICE_URL", "http://localhost:8002"),
    "slots": os.getenv("SLOT_SERVICE_URL", "http://localhost:8003"),
    "store": os.getenv("STORE_OPS_SERVICE_URL", "http://localhost:8004"),
    "inventory": os.getenv("INVENTORY_SERVICE_URL", "http://localhost:8005"),
    "notifications": os.getenv("NOTIFICATION_SERVICE_URL", "http://localhost:8006"),
    "analytics": os.getenv("ANALYTICS_SERVICE_URL", "http://localhost:8007"),
}
logger = configure_logging("api-gateway")

app = FastAPI(
    title="PeakPick API Gateway",
    version="0.1.0",
    description="Single entry point for PeakPick demo clients.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin.strip()
        for origin in os.getenv(
            "CORS_ORIGINS",
            "http://localhost:5173,http://127.0.0.1:5173",
        ).split(",")
        if origin.strip()
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
install_api_logging(app, logger, "api-gateway")


def _required_roles(service: str, path: str, method: str) -> set[str]:
    if service == "identity":
        return set()
    if service == "store" and method != "GET":
        return {"admin", "store_manager"}
    if service == "inventory" and method != "GET":
        return {"admin", "store_manager"}
    if service in {"notifications", "analytics"}:
        return {"admin", "store_manager"}
    if service == "slots" and method != "GET":
        return {"admin", "store_manager"}
    return set()


def _authorize(request: Request, service: str, path: str) -> AuthPrincipal | None:
    required_roles = _required_roles(service, path, request.method)
    if not required_roles:
        authorization = request.headers.get("authorization")
        return principal_from_authorization(authorization) if authorization else None

    principal = principal_from_authorization(request.headers.get("authorization"))
    if principal.role not in required_roles:
        raise HTTPException(status_code=403, detail="Role is not allowed for this API")
    return principal


def _tenant_headers(request: Request, principal: AuthPrincipal | None) -> dict[str, str]:
    if not principal:
        return {}

    if principal.role == "admin":
        store_id = request.headers.get("x-store-id") or request.query_params.get("store_id") or principal.store_id
    else:
        requested_store_id = request.headers.get("x-store-id") or request.query_params.get("store_id")
        if requested_store_id and requested_store_id != principal.store_id:
            raise HTTPException(status_code=403, detail="Store manager can only access their own store")
        store_id = principal.store_id or DEFAULT_STORE_ID

    return {
        "x-user-id": principal.username,
        "x-user-role": principal.role,
        "x-store-id": store_id,
    }


@app.get("/health")
async def health() -> dict[str, object]:
    return {"status": "ok", "service": "api-gateway", "routes": sorted(SERVICE_ROUTES)}


@app.get("/routes")
async def routes() -> dict[str, str]:
    return SERVICE_ROUTES


@app.get("/health/dependencies")
async def dependency_health() -> dict[str, object]:
    statuses: dict[str, object] = {}
    async with httpx.AsyncClient(timeout=3) as client:
        for service, base_url in SERVICE_ROUTES.items():
            try:
                response = await client.get(f"{base_url}/health")
                statuses[service] = {
                    "status_code": response.status_code,
                    "body": response.json(),
                }
            except httpx.HTTPError as exc:
                statuses[service] = {"status": "unreachable", "error": str(exc)}
    return {"service": "api-gateway", "dependencies": statuses}


@app.api_route("/{service}/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def proxy(service: str, path: str, request: Request) -> Response:
    if service not in SERVICE_ROUTES:
        raise HTTPException(status_code=404, detail=f"Unknown service route: {service}")

    principal = _authorize(request, service, path)
    target_url = f"{SERVICE_ROUTES[service].rstrip('/')}/{path}"
    headers = {key: value for key, value in request.headers.items() if key.lower() != "host"}
    headers.update(_tenant_headers(request, principal))
    body = await request.body()

    async with httpx.AsyncClient(timeout=10) as client:
        try:
            response = await client.request(
                method=request.method,
                url=target_url,
                params=request.query_params,
                content=body,
                headers=headers,
            )
        except httpx.HTTPError as exc:
            raise HTTPException(
                status_code=502,
                detail=f"{service} service is unavailable: {exc}",
            ) from exc

    return Response(
        content=response.content,
        status_code=response.status_code,
        media_type=response.headers.get("content-type"),
    )
