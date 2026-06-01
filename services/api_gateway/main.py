from __future__ import annotations

import os

import httpx
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware


SERVICE_ROUTES = {
    "catalog": os.getenv("CATALOG_SERVICE_URL", "http://localhost:8001"),
    "orders": os.getenv("ORDER_SERVICE_URL", "http://localhost:8002"),
    "slots": os.getenv("SLOT_SERVICE_URL", "http://localhost:8003"),
    "store": os.getenv("STORE_OPS_SERVICE_URL", "http://localhost:8004"),
    "inventory": os.getenv("INVENTORY_SERVICE_URL", "http://localhost:8005"),
    "notifications": os.getenv("NOTIFICATION_SERVICE_URL", "http://localhost:8006"),
    "analytics": os.getenv("ANALYTICS_SERVICE_URL", "http://localhost:8007"),
}

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

    target_url = f"{SERVICE_ROUTES[service].rstrip('/')}/{path}"
    headers = {key: value for key, value in request.headers.items() if key.lower() != "host"}
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
