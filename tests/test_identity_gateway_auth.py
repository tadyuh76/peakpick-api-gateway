from fastapi.testclient import TestClient

from services.api_gateway.main import app as gateway_app
from services.identity_service.main import app as identity_app


identity_client = TestClient(identity_app)
gateway_client = TestClient(gateway_app)


def test_identity_login_returns_demo_manager_token() -> None:
    response = identity_client.post(
        "/auth/login",
        json={"username": "manager.ueh@peakpick.local", "password": "manager123"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["access_token"]
    assert body["user"]["role"] == "store_manager"
    assert body["user"]["store_id"] == "store-ueh"


def test_gateway_rejects_admin_action_without_token() -> None:
    response = gateway_client.post("/store/orders/order-1/preparing")

    assert response.status_code == 401


def test_gateway_blocks_manager_from_other_store() -> None:
    login_response = identity_client.post(
        "/auth/login",
        json={"username": "manager.ueh@peakpick.local", "password": "manager123"},
    )
    token = login_response.json()["access_token"]

    response = gateway_client.patch(
        "/slots/pickup-windows/12:00-12:15?store_id=store-d1",
        headers={"Authorization": f"Bearer {token}"},
        json={"capacity": 12},
    )

    assert response.status_code == 403
