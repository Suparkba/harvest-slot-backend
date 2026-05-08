def get_token(client, email: str, password: str) -> str:
    response = client.post(
        "/api/v1/auth/token",
        data={"username": email, "password": password},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def test_customer_login_api(client):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "customer@test.com", "password": "demo1234!"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["data"]["role"] == "CUSTOMER"
    assert body["data"]["access_token"]


def test_owner_login_api(client):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "owner@test.com", "password": "demo1234!"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["data"]["role"] == "OWNER"
    assert body["data"]["access_token"]


def test_customer_reservation_order_payment_and_owner_procurement_decision_flow(client):
    customer_token = get_token(client, "customer@test.com", "demo1234!")
    owner_token = get_token(client, "owner@test.com", "demo1234!")
    customer_headers = {"Authorization": f"Bearer {customer_token}"}
    owner_headers = {"Authorization": f"Bearer {owner_token}"}

    reservation_response = client.post(
        "/api/v1/reservations",
        json={"items": [{"slot_id": 1, "package_count": 1}]},
        headers=customer_headers,
    )
    assert reservation_response.status_code == 200
    reservation_data = reservation_response.json()["data"]
    reservation_id = reservation_data["reservation_id"]
    assert reservation_data["items"][0]["product_name"] == "Test Apple Box"
    assert reservation_data["items"][0]["farm_name"] == "Test Farm"

    my_reservations_response = client.get("/api/v1/me/reservations", headers=customer_headers)
    assert my_reservations_response.status_code == 200
    reservation_row = next(
        row for row in my_reservations_response.json()["data"] if row["reservation_id"] == reservation_id
    )
    assert reservation_row["customer_name"] == "Test Customer"
    assert reservation_row["total_amount"] == 39000

    order_response = client.post(
        "/api/v1/orders/from-reservation",
        json={
            "reservation_id": reservation_id,
            "receiver_name": "Test Customer",
            "receiver_phone": "010-1111-2222",
            "shipping_address": "Seoul Test Address",
            "delivery_memo": "Call first",
        },
        headers=customer_headers,
    )
    assert order_response.status_code == 200
    order_id = order_response.json()["data"]["order_id"]

    payment_response = client.post(
        "/api/v1/payments/mock-approve",
        json={"order_id": order_id, "idempotency_key": f"test-payment-{order_id}"},
        headers=customer_headers,
    )
    assert payment_response.status_code == 200
    payment_data = payment_response.json()["data"]
    assert payment_data["payment_status"] == "APPROVED"
    assert payment_data["order_status"] == "PROCUREMENT_REQUESTED"
    procurement_id = payment_data["procurement_id"]

    procurements_response = client.get("/api/v1/owner/procurements", headers=owner_headers)
    assert procurements_response.status_code == 200
    procurement_row = next(
        row for row in procurements_response.json()["data"] if row["procurement_id"] == procurement_id
    )
    assert procurement_row["order_no"]
    assert procurement_row["customer_name"] == "Test Customer"
    assert procurement_row["total_amount"] == 39000
    procurement_item = procurement_row["items"][0]

    decision_response = client.patch(
        f"/api/v1/owner/procurements/{procurement_id}/decision",
        json={
            "decision": "APPROVED",
            "items": [
                {
                    "procurement_item_id": procurement_item["procurement_item_id"],
                    "approved_package_count": 1,
                    "approved_kg": 5.0,
                    "owner_memo": "Approved for shipping",
                }
            ],
            "rejected_reason": None,
        },
        headers=owner_headers,
    )
    assert decision_response.status_code == 200
    decision_data = decision_response.json()["data"]
    assert decision_data["procurement_status"] == "APPROVED"
    assert decision_data["items"][0]["approved_kg"] == 5.0


def test_owner_api_with_customer_token_returns_403(client):
    customer_token = get_token(client, "customer@test.com", "demo1234!")
    response = client.get(
        "/api/v1/owner/dashboard",
        headers={"Authorization": f"Bearer {customer_token}"},
    )
    assert response.status_code == 403
    body = response.json()
    assert body["message"] == "forbidden"
    assert body["error"] == "forbidden"


def test_owner_shipment_flow_and_customer_shipment_lookup(client):
    customer_token = get_token(client, "customer@test.com", "demo1234!")
    owner_token = get_token(client, "owner@test.com", "demo1234!")
    customer_headers = {"Authorization": f"Bearer {customer_token}"}
    owner_headers = {"Authorization": f"Bearer {owner_token}"}

    reservation_response = client.post(
        "/api/v1/reservations",
        json={"items": [{"slot_id": 1, "package_count": 1}]},
        headers=customer_headers,
    )
    assert reservation_response.status_code == 200
    reservation_id = reservation_response.json()["data"]["reservation_id"]

    order_response = client.post(
        "/api/v1/orders/from-reservation",
        json={
            "reservation_id": reservation_id,
            "receiver_name": "Shipment Customer",
            "receiver_phone": "010-5555-6666",
            "shipping_address": "Seoul Shipment Address",
            "delivery_memo": "shipment flow test",
        },
        headers=customer_headers,
    )
    assert order_response.status_code == 200
    order_id = order_response.json()["data"]["order_id"]

    payment_response = client.post(
        "/api/v1/payments/mock-approve",
        json={"order_id": order_id, "idempotency_key": f"shipment-payment-{order_id}"},
        headers=customer_headers,
    )
    assert payment_response.status_code == 200
    assert payment_response.json()["data"]["procurement_id"] >= 1

    procurement_response = client.get("/api/v1/owner/procurements", headers=owner_headers)
    assert procurement_response.status_code == 200
    procurement_row = next(row for row in procurement_response.json()["data"] if row["order_id"] == order_id)
    procurement_item = procurement_row["items"][0]

    decision_response = client.patch(
        f"/api/v1/owner/procurements/{procurement_row['procurement_id']}/decision",
        json={
            "decision": "APPROVED",
            "items": [
                {
                    "procurement_item_id": procurement_item["procurement_item_id"],
                    "approved_package_count": procurement_item["requested_package_count"],
                    "approved_kg": procurement_item["requested_kg"],
                    "owner_memo": "approved for shipment flow",
                }
            ],
            "rejected_reason": None,
        },
        headers=owner_headers,
    )
    assert decision_response.status_code == 200

    shipment_response = client.post(
        "/api/v1/owner/shipments",
        json={
            "order_id": order_id,
            "carrier_name": "CJ Logistics",
            "tracking_no": f"TRACK-{order_id}",
            "shipped_package_count": 1,
            "shipped_kg": 5.0,
        },
        headers=owner_headers,
    )
    assert shipment_response.status_code == 200
    shipment_data = shipment_response.json()["data"]
    assert shipment_data["shipment_status"] == "SHIPPED"
    shipment_id = shipment_data["shipment_id"]

    shipment_status_response = client.patch(
        f"/api/v1/owner/shipments/{shipment_id}/status",
        json={"shipment_status": "DELIVERED"},
        headers=owner_headers,
    )
    assert shipment_status_response.status_code == 200
    assert shipment_status_response.json()["data"]["shipment_status"] == "DELIVERED"

    customer_shipment_response = client.get(
        f"/api/v1/me/orders/{order_id}/shipment",
        headers=customer_headers,
    )
    assert customer_shipment_response.status_code == 200
    customer_shipment = customer_shipment_response.json()["data"]
    assert customer_shipment["shipment_id"] == shipment_id
    assert customer_shipment["shipment_status"] == "DELIVERED"
