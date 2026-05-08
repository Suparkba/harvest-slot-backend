"""
Live API E2E test for a running FastAPI server.

Before running this test, start the backend server first.
Example:

    uvicorn backend.app.main:app --reload

This test sends real HTTP requests to the running server and creates DB data.
It does not use FastAPI TestClient.
"""

from __future__ import annotations

import os
from uuid import uuid4

import httpx
import pytest


BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8000/api/v1")
TIMEOUT = 20.0
RUN_LIVE_API_TESTS = os.getenv("RUN_LIVE_API_TESTS", "").lower() == "true"

pytestmark = pytest.mark.skipif(
    not RUN_LIVE_API_TESTS,
    reason="set RUN_LIVE_API_TESTS=true to run live server HTTP E2E tests",
)


def _request(
    client: httpx.Client,
    method: str,
    path: str,
    *,
    expected_status: int,
    step: str,
    headers: dict[str, str] | None = None,
    json: dict | None = None,
) -> dict:
    url = f"{BASE_URL}{path}"
    try:
        response = client.request(method, url, headers=headers, json=json)
    except httpx.ConnectError as exc:
        raise AssertionError(
            f"{step}: live server connection failed. Start uvicorn first and verify BASE_URL={BASE_URL}"
        ) from exc
    except httpx.HTTPError as exc:
        raise AssertionError(f"{step}: live HTTP request failed for {url}: {exc}") from exc

    assert (
        response.status_code == expected_status
    ), f"{step}: expected {expected_status}, got {response.status_code}, body={response.text}"

    if response.headers.get("content-type", "").startswith("application/json"):
        return response.json()
    return {}


def _login(client: httpx.Client, email: str, password: str, *, step: str) -> tuple[str, dict]:
    body = _request(
        client,
        "POST",
        "/auth/login",
        expected_status=200,
        step=step,
        json={"email": email, "password": password},
    )
    token = body["data"]["access_token"]
    assert token, f"{step}: access_token is missing"
    return token, body


def test_live_customer_owner_e2e_flow():
    with httpx.Client(timeout=TIMEOUT) as client:
        health = _request(client, "GET", "/health", expected_status=200, step="health check")
        assert health["data"]["status"] == "ok", "health check: unexpected status payload"

        customer_token, customer_login = _login(
            client,
            "customer@test.com",
            "demo1234!",
            step="customer login",
        )
        assert customer_login["data"]["role"] == "CUSTOMER", "customer login: role should be CUSTOMER"
        customer_headers = {"Authorization": f"Bearer {customer_token}"}

        me = _request(
            client,
            "GET",
            "/me",
            expected_status=200,
            step="customer me",
            headers=customer_headers,
        )
        assert me["data"]["role"] == "CUSTOMER", "customer me: role should be CUSTOMER"

        products = _request(
            client,
            "GET",
            "/products",
            expected_status=200,
            step="products list",
        )
        product_rows = products["data"]
        assert product_rows, "products list: no products returned"
        product_id = product_rows[0]["product_id"]

        slots = _request(
            client,
            "GET",
            f"/products/{product_id}/slots",
            expected_status=200,
            step="product slots",
        )
        slot_rows = slots["data"]
        assert slot_rows, f"product slots: no open slots returned for product_id={product_id}"
        slot = slot_rows[0]
        slot_id = slot["slot_id"]
        assert slot["available_kg"] > 0, f"product slots: slot_id={slot_id} is not reservable"

        reservation = _request(
            client,
            "POST",
            "/reservations",
            expected_status=200,
            step="create reservation",
            headers=customer_headers,
            json={"items": [{"slot_id": slot_id, "package_count": 1}]},
        )
        reservation_id = reservation["data"]["reservation_id"]
        assert reservation_id, "create reservation: reservation_id missing"

        my_reservations = _request(
            client,
            "GET",
            "/me/reservations",
            expected_status=200,
            step="list my reservations",
            headers=customer_headers,
        )
        reservation_row = next(
            (row for row in my_reservations["data"] if row["reservation_id"] == reservation_id),
            None,
        )
        assert reservation_row is not None, f"list my reservations: reservation_id={reservation_id} not found"

        order = _request(
            client,
            "POST",
            "/orders/from-reservation",
            expected_status=200,
            step="create order from reservation",
            headers=customer_headers,
            json={
                "reservation_id": reservation_id,
                "receiver_name": "Live Test Customer",
                "receiver_phone": "010-2020-3030",
                "shipping_address": "Seoul Live Test Address",
                "delivery_memo": "live e2e test",
            },
        )
        order_id = order["data"]["order_id"]
        assert order_id, "create order from reservation: order_id missing"

        payment = _request(
            client,
            "POST",
            "/payments/mock-approve",
            expected_status=200,
            step="mock payment approve",
            headers=customer_headers,
            json={
                "order_id": order_id,
                "idempotency_key": f"live-payment-{uuid4()}",
            },
        )
        procurement_id = payment["data"]["procurement_id"]
        assert procurement_id, "mock payment approve: procurement_id missing"

        owner_token, owner_login = _login(
            client,
            "owner@test.com",
            "demo1234!",
            step="owner login",
        )
        assert owner_login["data"]["role"] == "OWNER", "owner login: role should be OWNER"
        owner_headers = {"Authorization": f"Bearer {owner_token}"}

        procurements = _request(
            client,
            "GET",
            "/owner/procurements",
            expected_status=200,
            step="owner procurements",
            headers=owner_headers,
        )
        procurement_row = next(
            (row for row in procurements["data"] if row["procurement_id"] == procurement_id),
            None,
        )
        assert procurement_row is not None, f"owner procurements: procurement_id={procurement_id} not found"
        assert procurement_row["items"], f"owner procurements: no procurement items for procurement_id={procurement_id}"

        procurement_decision = _request(
            client,
            "PATCH",
            f"/owner/procurements/{procurement_id}/decision",
            expected_status=200,
            step="owner procurement decision",
            headers=owner_headers,
            json={
                "decision": "APPROVED",
                "items": [
                    {
                        "procurement_item_id": item["procurement_item_id"],
                        "approved_package_count": item["requested_package_count"],
                        "approved_kg": item["requested_kg"],
                        "owner_memo": "approved in live e2e test",
                    }
                    for item in procurement_row["items"]
                ],
                "rejected_reason": None,
            },
        )
        assert (
            procurement_decision["data"]["procurement_status"] == "APPROVED"
        ), "owner procurement decision: procurement_status should be APPROVED"

        shipment = _request(
            client,
            "POST",
            "/owner/shipments",
            expected_status=200,
            step="create shipment",
            headers=owner_headers,
            json={
                "order_id": order_id,
                "carrier_name": "Live Express",
                "tracking_no": f"LIVE-{uuid4().hex[:10].upper()}",
                "shipped_package_count": 1,
                "shipped_kg": reservation_row["items"][0]["reserved_kg"],
            },
        )
        shipment_id = shipment["data"]["shipment_id"]
        assert shipment_id, "create shipment: shipment_id missing"

        shipment_status = _request(
            client,
            "PATCH",
            f"/owner/shipments/{shipment_id}/status",
            expected_status=200,
            step="update shipment status",
            headers=owner_headers,
            json={"shipment_status": "DELIVERED"},
        )
        assert (
            shipment_status["data"]["shipment_status"] == "DELIVERED"
        ), "update shipment status: shipment_status should be DELIVERED"

        customer_token, _ = _login(
            client,
            "customer@test.com",
            "demo1234!",
            step="customer relogin before return",
        )
        customer_headers = {"Authorization": f"Bearer {customer_token}"}

        return_create = _request(
            client,
            "POST",
            "/returns",
            expected_status=200,
            step="create return request",
            headers=customer_headers,
            json={
                "order_id": order_id,
                "reason_code": "QUALITY_ISSUE",
                "reason_detail": "live e2e return request",
                "requested_amount": reservation_row["total_amount"],
            },
        )
        return_request_id = return_create["data"]["return_request_id"]
        assert return_request_id, "create return request: return_request_id missing"

        my_returns = _request(
            client,
            "GET",
            "/me/returns",
            expected_status=200,
            step="list my returns after request",
            headers=customer_headers,
        )
        my_return_row = next(
            (row for row in my_returns["data"] if row["return_request_id"] == return_request_id),
            None,
        )
        assert my_return_row is not None, f"list my returns: return_request_id={return_request_id} not found"

        owner_token, _ = _login(
            client,
            "owner@test.com",
            "demo1234!",
            step="owner relogin before return decision",
        )
        owner_headers = {"Authorization": f"Bearer {owner_token}"}

        return_decision = _request(
            client,
            "PATCH",
            f"/owner/returns/{return_request_id}/decision",
            expected_status=200,
            step="owner return decision",
            headers=owner_headers,
            json={
                "decision": "APPROVED",
                "approved_amount": reservation_row["total_amount"],
                "decision_reason": "approved in live e2e test",
            },
        )
        assert (
            return_decision["data"]["return_status"] == "REFUNDED"
        ), "owner return decision: return_status should be REFUNDED"

        customer_token, _ = _login(
            client,
            "customer@test.com",
            "demo1234!",
            step="customer relogin before final verification",
        )
        customer_headers = {"Authorization": f"Bearer {customer_token}"}

        order_detail = _request(
            client,
            "GET",
            f"/me/orders/{order_id}",
            expected_status=200,
            step="final order detail",
            headers=customer_headers,
        )
        assert order_detail["data"]["order_status"] == "REFUNDED", "final order detail: order_status should be REFUNDED"
        assert (
            order_detail["data"]["shipment"]["shipment_status"] == "DELIVERED"
        ), "final order detail: shipment_status should be DELIVERED"
        assert (
            order_detail["data"]["return_request"]["return_status"] == "REFUNDED"
        ), "final order detail: return_status should be REFUNDED"

        final_returns = _request(
            client,
            "GET",
            "/me/returns",
            expected_status=200,
            step="final my returns",
            headers=customer_headers,
        )
        final_return_row = next(
            (row for row in final_returns["data"] if row["return_request_id"] == return_request_id),
            None,
        )
        assert final_return_row is not None, f"final my returns: return_request_id={return_request_id} not found"
        assert final_return_row["refund_status"] == "COMPLETED", "final my returns: refund_status should be COMPLETED"
