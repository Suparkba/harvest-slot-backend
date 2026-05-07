from datetime import datetime, timedelta

from backend.app.models.order import Order, OrderItem
from backend.app.models.payment import Payment
from backend.app.models.procurement import Procurement
from backend.app.models.reservation import Reservation, ReservationItem
from backend.app.models.return_refund import Refund, ReturnRequest


def login_headers(client, email: str, password: str) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/token",
        data={"username": email, "password": password},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def seed_delivered_order(db_session, *, payment_approved_amount: int = 39000) -> dict[str, int]:
    now = datetime.utcnow()

    reservation = Reservation(
        reservation_id=1,
        customer_id=101,
        reservation_no="RSV-RETURN-1",
        reservation_status="ORDERED",
        reserved_until=now + timedelta(days=1),
        total_reserved_kg=5.0,
        total_amount=39000,
    )
    db_session.add(reservation)
    db_session.flush()

    reservation_item = ReservationItem(
        reservation_item_id=1,
        reservation_id=reservation.reservation_id,
        slot_id=1,
        package_count=1,
        reserved_kg=5.0,
        unit_price_snapshot=39000,
        subtotal_amount=39000,
        created_at=now,
    )
    db_session.add(reservation_item)
    db_session.flush()

    order = Order(
        order_id=1,
        reservation_id=reservation.reservation_id,
        order_no="ORD-RETURN-1",
        order_status="DELIVERED",
        total_amount=39000,
        receiver_name="Test Customer",
        receiver_phone="010-1111-2222",
        shipping_address="Seoul Test Address",
        delivery_memo="Leave at door",
        ordered_at=now,
        paid_at=now,
    )
    db_session.add(order)
    db_session.flush()

    order_item = OrderItem(
        order_item_id=1,
        order_id=order.order_id,
        reservation_item_id=reservation_item.reservation_item_id,
        package_count=1,
        ordered_kg=5.0,
        unit_price=39000,
        subtotal_amount=39000,
        order_item_status="DELIVERED",
    )
    db_session.add(order_item)

    payment = Payment(
        payment_id=1,
        order_id=order.order_id,
        payment_provider="MOCK",
        payment_method="MOCK_CARD",
        payment_status="APPROVED",
        requested_amount=39000,
        approved_amount=payment_approved_amount,
        mock_transaction_key="mock-return-tx-1",
        idempotency_key=f"return-payment-{payment_approved_amount}",
        requested_at=now,
        approved_at=now,
    )
    db_session.add(payment)

    procurement = Procurement(
        procurement_id=1,
        order_id=order.order_id,
        farm_id=1,
        owner_id=1,
        procurement_no="PRC-RETURN-1",
        procurement_status="APPROVED",
        requested_at=now,
        response_deadline_at=now + timedelta(days=1),
        decided_at=now,
    )
    db_session.add(procurement)
    db_session.commit()

    return {"order_id": order.order_id, "payment_id": payment.payment_id}


def test_return_approval_creates_refund_and_duplicate_decision_returns_400(client, db_session):
    seeded = seed_delivered_order(db_session)
    customer_headers = login_headers(client, "customer@test.com", "demo1234!")

    create_response = client.post(
        "/api/v1/returns",
        json={
            "order_id": seeded["order_id"],
            "reason_code": "DAMAGED",
            "reason_detail": "Box damaged on arrival",
            "requested_amount": 39000,
        },
        headers=customer_headers,
    )
    assert create_response.status_code == 200
    create_body = create_response.json()
    assert set(create_body.keys()) == {"data", "message", "error"}
    return_request_id = create_body["data"]["return_request_id"]

    decision_payload = {
        "decision": "APPROVED",
        "approved_amount": 39000,
        "decision_reason": "Approved after review",
    }
    approve_response = client.patch(
        f"/api/v1/owner/returns/{return_request_id}/decision",
        json=decision_payload,
        headers={"Authorization": "Bearer mock-owner-token"},
    )
    assert approve_response.status_code == 200
    approve_body = approve_response.json()
    assert approve_body["data"]["return_status"] == "REFUNDED"
    assert approve_body["data"]["approved_amount"] == 39000
    assert approve_body["data"]["refund"]["refund_status"] == "COMPLETED"
    assert approve_body["data"]["refund"]["refunded_amount"] == 39000

    duplicate_response = client.patch(
        f"/api/v1/owner/returns/{return_request_id}/decision",
        json=decision_payload,
        headers={"Authorization": "Bearer mock-owner-token"},
    )
    assert duplicate_response.status_code == 400
    duplicate_body = duplicate_response.json()
    assert set(duplicate_body.keys()) == {"data", "message", "error"}
    assert duplicate_body["message"] == "return request already decided"
    assert duplicate_body["error"] == "return request already decided"


def test_return_approval_rejects_when_refund_already_exists(client, db_session):
    seeded = seed_delivered_order(db_session)
    now = datetime.utcnow()

    return_request = ReturnRequest(
        return_request_id=1,
        order_id=seeded["order_id"],
        return_no="RET-EXISTING-1",
        return_status="REQUESTED",
        reason_code="DAMAGED",
        reason_detail="Existing refund row",
        evidence_image_url=None,
        requested_amount=39000,
        approved_amount=0,
        decision_reason=None,
        requested_at=now,
        decided_at=None,
    )
    db_session.add(return_request)
    db_session.flush()

    refund = Refund(
        refund_id=1,
        return_request_id=return_request.return_request_id,
        payment_id=seeded["payment_id"],
        refund_status="COMPLETED",
        requested_amount=39000,
        refunded_amount=39000,
        requested_at=now,
        completed_at=now,
        failure_reason=None,
    )
    db_session.add(refund)
    db_session.commit()

    response = client.patch(
        f"/api/v1/owner/returns/{return_request.return_request_id}/decision",
        json={"decision": "APPROVED", "approved_amount": 39000},
        headers={"Authorization": "Bearer mock-owner-token"},
    )
    assert response.status_code == 400
    body = response.json()
    assert body["message"] == "refund already exists"
    assert body["error"] == "refund already exists"


def test_return_approval_validates_requested_amount_and_payment_amount(client, db_session):
    seeded = seed_delivered_order(db_session, payment_approved_amount=20000)
    customer_headers = login_headers(client, "customer@test.com", "demo1234!")

    create_response = client.post(
        "/api/v1/returns",
        json={
            "order_id": seeded["order_id"],
            "reason_code": "DAMAGED",
            "requested_amount": 39000,
        },
        headers=customer_headers,
    )
    return_request_id = create_response.json()["data"]["return_request_id"]

    requested_amount_response = client.patch(
        f"/api/v1/owner/returns/{return_request_id}/decision",
        json={"decision": "APPROVED", "approved_amount": 40000},
        headers={"Authorization": "Bearer mock-owner-token"},
    )
    assert requested_amount_response.status_code == 400
    requested_amount_body = requested_amount_response.json()
    assert requested_amount_body["message"] == "approved amount exceeds requested amount"

    payment_amount_response = client.patch(
        f"/api/v1/owner/returns/{return_request_id}/decision",
        json={"decision": "APPROVED", "approved_amount": 30000},
        headers={"Authorization": "Bearer mock-owner-token"},
    )
    assert payment_amount_response.status_code == 400
    payment_amount_body = payment_amount_response.json()
    assert payment_amount_body["message"] == "approved amount exceeds payment amount"


def test_owner_and_customer_return_lists_show_decided_status(client, db_session):
    seeded = seed_delivered_order(db_session)
    customer_headers = login_headers(client, "customer@test.com", "demo1234!")

    create_response = client.post(
        "/api/v1/returns",
        json={
            "order_id": seeded["order_id"],
            "reason_code": "DAMAGED",
            "requested_amount": 39000,
        },
        headers=customer_headers,
    )
    return_request_id = create_response.json()["data"]["return_request_id"]

    approve_response = client.patch(
        f"/api/v1/owner/returns/{return_request_id}/decision",
        json={"decision": "APPROVED", "approved_amount": 39000},
        headers={"Authorization": "Bearer mock-owner-token"},
    )
    assert approve_response.status_code == 200

    order_detail_response = client.get(f"/api/v1/me/orders/{seeded['order_id']}", headers=customer_headers)
    assert order_detail_response.status_code == 200
    order_detail = order_detail_response.json()["data"]
    assert order_detail["order_status"] == "REFUNDED"
    assert order_detail["payments"][0]["payment_status"] == "REFUNDED"
    assert order_detail["order_items"][0]["order_item_status"] == "REFUNDED"
    assert order_detail["return_request"]["return_status"] == "REFUNDED"
    assert order_detail["return_request"]["refund"]["refund_status"] == "COMPLETED"
    assert order_detail["refund"]["refunded_amount"] == 39000

    owner_list_response = client.get(
        "/api/v1/owner/returns",
        headers={"Authorization": "Bearer mock-owner-token"},
    )
    assert owner_list_response.status_code == 200
    owner_row = next(
        row for row in owner_list_response.json()["data"] if row["return_request_id"] == return_request_id
    )
    assert owner_row["return_status"] == "REFUNDED"
    assert owner_row["refund"]["refunded_amount"] == 39000

    customer_list_response = client.get("/api/v1/me/returns", headers=customer_headers)
    assert customer_list_response.status_code == 200
    customer_row = next(
        row for row in customer_list_response.json()["data"] if row["return_request_id"] == return_request_id
    )
    assert customer_row["return_status"] == "REFUNDED"
    assert customer_row["refund"]["refund_status"] == "COMPLETED"
