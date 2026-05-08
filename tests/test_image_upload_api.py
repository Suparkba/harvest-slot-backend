from datetime import datetime, timedelta
from io import BytesIO

from fastapi import HTTPException

from backend.app.models.account import Account, OwnerProfile
from backend.app.models.farm import Farm
from backend.app.models.order import Order, OrderItem
from backend.app.models.procurement import Procurement, ProcurementItem
from backend.app.models.product import Product
from backend.app.models.reservation import Reservation, ReservationItem
from backend.app.services.image_storage_service import ImageStorageService


def _owner_headers() -> dict[str, str]:
    return {"Authorization": "Bearer mock-owner-token"}


def _customer_headers() -> dict[str, str]:
    return {"Authorization": "Bearer mock-customer-token"}


def _seed_procurement_item(db_session) -> int:
    now = datetime.utcnow()

    reservation = Reservation(
        reservation_id=11,
        customer_id=101,
        reservation_no="RSV-IMG-11",
        reservation_status="ORDERED",
        reserved_until=now + timedelta(days=1),
        total_reserved_kg=5.0,
        total_amount=39000,
    )
    db_session.add(reservation)
    db_session.flush()

    reservation_item = ReservationItem(
        reservation_item_id=11,
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
        order_id=11,
        reservation_id=reservation.reservation_id,
        order_no="ORD-IMG-11",
        order_status="PROCUREMENT_REQUESTED",
        total_amount=39000,
        receiver_name="Image Test Customer",
        receiver_phone="010-1111-3333",
        shipping_address="Seoul Image Address",
        delivery_memo="image upload test",
        ordered_at=now,
        paid_at=now,
    )
    db_session.add(order)
    db_session.flush()

    order_item = OrderItem(
        order_item_id=11,
        order_id=order.order_id,
        reservation_item_id=reservation_item.reservation_item_id,
        package_count=1,
        ordered_kg=5.0,
        unit_price=39000,
        subtotal_amount=39000,
        order_item_status="PROCUREMENT_REQUESTED",
    )
    db_session.add(order_item)
    db_session.flush()

    procurement = Procurement(
        procurement_id=11,
        order_id=order.order_id,
        farm_id=1,
        owner_id=1,
        procurement_no="PRC-IMG-11",
        procurement_status="APPROVED",
        requested_at=now,
        response_deadline_at=now + timedelta(days=1),
        decided_at=now,
    )
    db_session.add(procurement)
    db_session.flush()

    procurement_item = ProcurementItem(
        procurement_item_id=11,
        procurement_id=procurement.procurement_id,
        order_item_id=order_item.order_item_id,
        requested_package_count=1,
        requested_kg=5.0,
        approved_package_count=1,
        approved_kg=5.0,
        approval_status="APPROVED",
        owner_memo="ready for quality inspection",
    )
    db_session.add(procurement_item)
    db_session.commit()
    return procurement_item.procurement_item_id


def _seed_other_owner_product(db_session) -> int:
    other_account = Account(
        account_id=3,
        email="owner2@test.com",
        password_hash="hashed",
        role="OWNER",
        status="ACTIVE",
        email_verified=True,
    )
    db_session.add(other_account)
    db_session.flush()

    other_profile = OwnerProfile(
        owner_id=2,
        account_id=other_account.account_id,
        owner_name="Other Owner",
        owner_phone="010-2222-3333",
    )
    db_session.add(other_profile)
    db_session.flush()

    other_farm = Farm(
        farm_id=2,
        owner_id=other_profile.owner_id,
        farm_name="Other Farm",
        farm_region="Busan",
        farm_address="Other Address",
    )
    db_session.add(other_farm)
    db_session.flush()

    other_product = Product(
        product_id=2,
        farm_id=other_farm.farm_id,
        product_name="Other Apple Box",
        fruit_type="APPLE",
        variety="Fuji",
        package_unit_kg=5.0,
        base_price=45000,
        product_status="ACTIVE",
    )
    db_session.add(other_product)
    db_session.commit()
    return other_product.product_id


def test_images_upload_api_returns_403_for_customer_token(client):
    response = client.post(
        "/api/v1/images/upload",
        headers=_customer_headers(),
        files={"file": ("apple.jpg", BytesIO(b"fake-image"), "image/jpeg")},
    )
    assert response.status_code == 403
    assert response.json()["message"] == "forbidden"


def test_owner_product_image_upload_returns_403_for_customer_token(client):
    response = client.post(
        "/api/v1/owner/products/1/image",
        headers=_customer_headers(),
        files={"file": ("apple.jpg", BytesIO(b"fake-image"), "image/jpeg")},
    )
    assert response.status_code == 403
    assert response.json()["message"] == "forbidden"


def test_images_crud_owner_endpoints_work_with_mocked_storage(client, monkeypatch):
    def fake_upload(self, upload, *, product_seq=None, subfolder=None):
        return {
            "file_url": "https://cdn.test/images/products/1/uploaded.jpg",
            "file_name": "uploaded.jpg",
            "file_type": "image",
            "subfolder": subfolder or "products/1",
        }

    def fake_list(self, *, subfolder=None):
        return {
            "subfolder": subfolder or "products/1",
            "count": 1,
            "files": [
                {
                    "file_name": "uploaded.jpg",
                    "file_type": "image",
                    "subfolder": subfolder or "products/1",
                    "file_url": "https://cdn.test/images/products/1/uploaded.jpg",
                    "file_size": 1024,
                    "modified_at": "2026-05-08T10:30:00+09:00",
                }
            ],
        }

    def fake_get(self, file_name, *, subfolder=None):
        return {
            "file_name": file_name,
            "file_type": "image",
            "subfolder": subfolder or "products/1",
            "file_url": "https://cdn.test/images/products/1/uploaded.jpg",
            "file_size": 1024,
            "modified_at": "2026-05-08T10:30:00+09:00",
        }

    def fake_update(self, file_name, upload, *, subfolder=None):
        return {
            "file_url": "https://cdn.test/images/products/1/uploaded.jpg",
            "file_name": file_name,
            "file_type": "image",
            "subfolder": subfolder or "products/1",
        }

    def fake_delete(self, file_name, *, subfolder=None):
        return {"file_name": file_name, "subfolder": subfolder or "products/1"}

    monkeypatch.setattr(ImageStorageService, "upload_image", fake_upload)
    monkeypatch.setattr(ImageStorageService, "list_images", fake_list)
    monkeypatch.setattr(ImageStorageService, "get_image", fake_get)
    monkeypatch.setattr(ImageStorageService, "update_image", fake_update)
    monkeypatch.setattr(ImageStorageService, "delete_image", fake_delete)

    upload_response = client.post(
        "/api/v1/images/upload",
        headers=_owner_headers(),
        data={"product_seq": 1, "subfolder": "products/1"},
        files={"file": ("apple.jpg", BytesIO(b"fake-image"), "image/jpeg")},
    )
    assert upload_response.status_code == 200
    assert upload_response.json()["data"]["file_url"] == "https://cdn.test/images/products/1/uploaded.jpg"

    list_response = client.get("/api/v1/images", headers=_owner_headers(), params={"subfolder": "products/1"})
    assert list_response.status_code == 200
    assert list_response.json()["data"]["count"] == 1

    get_response = client.get(
        "/api/v1/images/uploaded.jpg",
        headers=_owner_headers(),
        params={"subfolder": "products/1"},
    )
    assert get_response.status_code == 200
    assert get_response.json()["data"]["file_name"] == "uploaded.jpg"

    update_response = client.put(
        "/api/v1/images/uploaded.jpg",
        headers=_owner_headers(),
        data={"subfolder": "products/1"},
        files={"file": ("updated.jpg", BytesIO(b"new-image"), "image/jpeg")},
    )
    assert update_response.status_code == 200
    assert update_response.json()["data"]["file_name"] == "uploaded.jpg"

    delete_response = client.delete(
        "/api/v1/images/uploaded.jpg",
        headers=_owner_headers(),
        params={"subfolder": "products/1"},
    )
    assert delete_response.status_code == 200
    assert delete_response.json()["data"]["file_name"] == "uploaded.jpg"


def test_owner_product_image_upload_updates_image_url(client, db_session, monkeypatch):
    def fake_upload(self, upload, *, product_seq=None, subfolder=None):
        assert product_seq == 1
        assert subfolder == "products/1"
        return {
            "file_url": "https://cdn.test/products/1/product_1_test.jpg",
            "file_name": "product_1_test.jpg",
            "file_type": "image",
            "subfolder": subfolder,
        }

    monkeypatch.setattr(ImageStorageService, "upload_image", fake_upload)

    response = client.post(
        "/api/v1/owner/products/1/image",
        headers=_owner_headers(),
        files={"file": ("apple.jpg", BytesIO(b"fake-image-bytes"), "image/jpeg")},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["data"]["product_id"] == 1
    assert body["data"]["image_url"] == "https://cdn.test/products/1/product_1_test.jpg"
    assert body["data"]["file_name"] == "product_1_test.jpg"
    assert body["data"]["subfolder"] == "products/1"
    assert db_session.get(Product, 1).image_url == "https://cdn.test/products/1/product_1_test.jpg"


def test_owner_product_image_upload_failure_does_not_update_image_url(client, db_session, monkeypatch):
    original_image_url = db_session.get(Product, 1).image_url

    def failing_upload(self, upload, *, product_seq=None, subfolder=None):
        raise HTTPException(status_code=502, detail="image storage error")

    monkeypatch.setattr(ImageStorageService, "upload_image", failing_upload)

    response = client.post(
        "/api/v1/owner/products/1/image",
        headers=_owner_headers(),
        files={"file": ("apple.jpg", BytesIO(b"fake-image-bytes"), "image/jpeg")},
    )
    assert response.status_code == 502
    assert db_session.get(Product, 1).image_url == original_image_url


def test_other_owner_product_image_upload_is_blocked(client, db_session, monkeypatch):
    other_product_id = _seed_other_owner_product(db_session)
    called = {"value": False}

    def fake_upload(self, upload, *, product_seq=None, subfolder=None):
        called["value"] = True
        return {
            "file_url": "https://cdn.test/blocked.jpg",
            "file_name": "blocked.jpg",
            "file_type": "image",
            "subfolder": subfolder,
        }

    monkeypatch.setattr(ImageStorageService, "upload_image", fake_upload)

    response = client.post(
        f"/api/v1/owner/products/{other_product_id}/image",
        headers=_owner_headers(),
        files={"file": ("apple.jpg", BytesIO(b"fake-image"), "image/jpeg")},
    )
    assert response.status_code == 404
    assert response.json()["message"] == "product not found"
    assert called["value"] is False


def test_owner_quality_image_upload_returns_image_url(client, db_session, monkeypatch):
    procurement_item_id = _seed_procurement_item(db_session)

    def fake_upload(self, upload, *, product_seq=None, subfolder=None):
        assert product_seq == 1
        assert subfolder == "quality-inspections/1"
        return {
            "file_url": "https://cdn.test/quality-inspections/1/quality_test.jpg",
            "file_name": "quality_test.jpg",
            "file_type": "image",
            "subfolder": subfolder,
        }

    monkeypatch.setattr(ImageStorageService, "upload_image", fake_upload)

    upload_response = client.post(
        "/api/v1/owner/quality-inspections/image",
        headers=_owner_headers(),
        files={"file": ("quality.jpg", BytesIO(b"quality-image"), "image/jpeg")},
    )
    assert upload_response.status_code == 200
    upload_body = upload_response.json()
    assert upload_body["data"]["image_url"] == "https://cdn.test/quality-inspections/1/quality_test.jpg"

    create_response = client.post(
        "/api/v1/owner/quality-inspections",
        headers=_owner_headers(),
        json={
            "procurement_item_id": procurement_item_id,
            "image_url": upload_body["data"]["image_url"],
            "owner_confirmed_grade": "A",
            "owner_decision": "PASS",
        },
    )
    assert create_response.status_code == 200
    create_body = create_response.json()
    assert create_body["data"]["procurement_item_id"] == procurement_item_id
    assert create_body["data"]["image_url"] == upload_body["data"]["image_url"]


def test_quality_inspection_create_keeps_existing_image_url_flow(client, db_session):
    procurement_item_id = _seed_procurement_item(db_session)

    response = client.post(
        "/api/v1/owner/quality-inspections",
        headers=_owner_headers(),
        json={
            "procurement_item_id": procurement_item_id,
            "image_url": "/mock/quality/apple_sample_001.jpg",
            "owner_confirmed_grade": "A",
            "owner_decision": "PASS",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["data"]["procurement_item_id"] == procurement_item_id
    assert body["data"]["image_url"] == "/mock/quality/apple_sample_001.jpg"
