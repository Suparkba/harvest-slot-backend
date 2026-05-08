from datetime import datetime, timedelta
from io import BytesIO

import httpx

from backend.app.core.config import settings
from backend.app.models.order import Order, OrderItem
from backend.app.models.procurement import Procurement, ProcurementItem
from backend.app.models.quality_inspection import QualityInspection
from backend.app.models.reservation import Reservation, ReservationItem
from backend.app.services.image_storage_service import ImageStorageService


def _owner_headers() -> dict[str, str]:
    return {"Authorization": "Bearer mock-owner-token"}


def _seed_procurement_item(db_session) -> int:
    now = datetime.utcnow()

    reservation = Reservation(
        reservation_id=21,
        customer_id=101,
        reservation_no="RSV-DL-21",
        reservation_status="ORDERED",
        reserved_until=now + timedelta(days=1),
        total_reserved_kg=5.0,
        total_amount=39000,
    )
    db_session.add(reservation)
    db_session.flush()

    reservation_item = ReservationItem(
        reservation_item_id=21,
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
        order_id=21,
        reservation_id=reservation.reservation_id,
        order_no="ORD-DL-21",
        order_status="PROCUREMENT_REQUESTED",
        total_amount=39000,
        receiver_name="DL Test Customer",
        receiver_phone="010-2121-2121",
        shipping_address="Seoul DL Address",
        delivery_memo="quality analyze test",
        ordered_at=now,
        paid_at=now,
    )
    db_session.add(order)
    db_session.flush()

    order_item = OrderItem(
        order_item_id=21,
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
        procurement_id=21,
        order_id=order.order_id,
        farm_id=1,
        owner_id=1,
        procurement_no="PRC-DL-21",
        procurement_status="APPROVED",
        requested_at=now,
        response_deadline_at=now + timedelta(days=1),
        decided_at=now,
    )
    db_session.add(procurement)
    db_session.flush()

    procurement_item = ProcurementItem(
        procurement_item_id=21,
        procurement_id=procurement.procurement_id,
        order_item_id=order_item.order_item_id,
        requested_package_count=1,
        requested_kg=5.0,
        approved_package_count=1,
        approved_kg=5.0,
        approval_status="APPROVED",
        owner_memo="quality analyze ready",
    )
    db_session.add(procurement_item)
    db_session.commit()
    return procurement_item.procurement_item_id


def test_quality_analyze_persist_image_defaults_to_false_and_skips_nas(client, db_session, monkeypatch):
    procurement_item_id = _seed_procurement_item(db_session)
    called = {"value": False}

    def should_not_upload(self, upload, *, product_seq=None, subfolder=None):
        called["value"] = True
        raise AssertionError("NAS upload should not be called when persist_image is false")

    monkeypatch.setattr(ImageStorageService, "upload_image", should_not_upload)

    response = client.post(
        "/api/v1/owner/quality-inspections/analyze",
        headers=_owner_headers(),
        json={
            "procurement_item_id": procurement_item_id,
            "image_url": "https://cdn.example.com/quality/apple_001.jpg",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["message"] == "quality analysis completed"
    assert body["data"]["procurement_item_id"] == procurement_item_id
    assert body["data"]["image_persisted"] is False
    assert body["data"]["image_url"] == "https://cdn.example.com/quality/apple_001.jpg"
    assert body["data"]["model_version"] == "mock-dl-v1"
    assert called["value"] is False


def test_quality_analyze_requires_procurement_item_id(client):
    response = client.post(
        "/api/v1/owner/quality-inspections/analyze",
        headers=_owner_headers(),
        json={"image_url": "https://cdn.example.com/quality/apple_001.jpg"},
    )
    assert response.status_code == 400
    assert response.json()["message"] == "procurement item not found"


def test_quality_analyze_persist_false_with_file_returns_null_image_url(client, db_session, monkeypatch):
    procurement_item_id = _seed_procurement_item(db_session)
    called = {"value": False}

    def should_not_upload(self, upload, *, product_seq=None, subfolder=None):
        called["value"] = True
        raise AssertionError("NAS upload should not be called when persist_image is false")

    monkeypatch.setattr(ImageStorageService, "upload_image", should_not_upload)

    response = client.post(
        "/api/v1/owner/quality-inspections/analyze",
        headers=_owner_headers(),
        data={"procurement_item_id": str(procurement_item_id)},
        files={"image": ("apple.jpg", BytesIO(b"analysis-image"), "image/jpeg")},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["data"]["image_persisted"] is False
    assert body["data"]["image_url"] is None
    assert called["value"] is False


def test_quality_analyze_persist_true_calls_nas_only_then_returns_image_url(client, db_session, monkeypatch):
    procurement_item_id = _seed_procurement_item(db_session)

    def fake_upload(self, upload, *, product_seq=None, subfolder=None):
        assert product_seq == procurement_item_id
        assert subfolder == "quality-inspections/1"
        return {
            "file_url": "https://cdn.test/quality-inspections/1/analyzed.jpg",
            "file_name": "analyzed.jpg",
            "file_type": "image",
            "subfolder": subfolder,
        }

    monkeypatch.setattr(ImageStorageService, "upload_image", fake_upload)

    response = client.post(
        "/api/v1/owner/quality-inspections/analyze",
        headers=_owner_headers(),
        data={"procurement_item_id": str(procurement_item_id), "persist_image": "true"},
        files={"image": ("apple.jpg", BytesIO(b"analysis-image"), "image/jpeg")},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["data"]["image_persisted"] is True
    assert body["data"]["image_url"] == "https://cdn.test/quality-inspections/1/analyzed.jpg"
    assert body["data"]["file_name"] == "analyzed.jpg"
    assert body["data"]["subfolder"] == "quality-inspections/1"


def test_quality_analyze_persist_true_requires_image_file(client, db_session):
    procurement_item_id = _seed_procurement_item(db_session)

    response = client.post(
        "/api/v1/owner/quality-inspections/analyze",
        headers=_owner_headers(),
        json={
            "procurement_item_id": procurement_item_id,
            "image_url": "https://cdn.example.com/quality/apple_003.jpg",
            "persist_image": True,
        },
    )
    assert response.status_code == 400
    assert response.json()["message"] == "image file required when persist_image is true"


def test_quality_analyze_does_not_insert_quality_inspection_row(client, db_session, monkeypatch):
    procurement_item_id = _seed_procurement_item(db_session)
    before_count = db_session.query(QualityInspection).count()

    monkeypatch.setattr(
        ImageStorageService,
        "upload_image",
        lambda self, upload, *, product_seq=None, subfolder=None: {
            "file_url": "https://cdn.test/quality-inspections/1/analyzed.jpg",
            "file_name": "analyzed.jpg",
            "file_type": "image",
            "subfolder": subfolder,
        },
    )

    response = client.post(
        "/api/v1/owner/quality-inspections/analyze",
        headers=_owner_headers(),
        data={"procurement_item_id": str(procurement_item_id), "persist_image": "true"},
        files={"image": ("apple.jpg", BytesIO(b"analysis-image"), "image/jpeg")},
    )
    assert response.status_code == 200
    after_count = db_session.query(QualityInspection).count()
    assert after_count == before_count


def test_quality_create_uses_mock_analysis_result(client, db_session):
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
    assert body["data"]["model_version"] == "mock-dl-v1"
    assert body["data"]["freshness_score"] == 91.2


def test_quality_analyze_calls_external_api_when_enabled_with_image_field(client, db_session, monkeypatch):
    procurement_item_id = _seed_procurement_item(db_session)

    class DummyResponse:
        status_code = 200

        @staticmethod
        def json():
            return {
                "data": {
                    "fruit_type": "apple",
                    "model_grade": "B",
                    "freshness_score": 82.1,
                    "color_score": 80.4,
                    "roundness_score": 84.9,
                    "bruise_probability": 0.12,
                    "model_decision": "PASS",
                    "action_required": "RETAKE",
                    "angle_label": "bottom",
                    "angle_confidence": 0.41,
                    "grade_confidence": 0.81,
                    "retake_reason": "wrong angle",
                    "model_version": "external-dl-v1",
                    "image_url": "/kaggle/working/uploads/apple.jpg",
                },
                "message": "dl quality ok",
                "error": None,
            }

    class DummyClient:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def post(self, url, files):
            assert url == "https://dl.example.com/analyze"
            assert "image" in files
            assert files["image"][0] == "apple.jpg"
            return DummyResponse()

    monkeypatch.setattr(settings, "dl_quality_enabled", True)
    monkeypatch.setattr(settings, "dl_quality_api_url", "https://dl.example.com/analyze")
    monkeypatch.setattr(httpx, "Client", DummyClient)

    response = client.post(
        "/api/v1/owner/quality-inspections/analyze",
        headers=_owner_headers(),
        data={"procurement_item_id": str(procurement_item_id)},
        files={"image": ("apple.jpg", BytesIO(b"dl-image"), "image/jpeg")},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["data"]["model_version"] == "external-dl-v1"
    assert body["data"]["model_grade"] == "B"
    assert body["data"]["freshness_score"] == 82.1
    assert body["data"]["action_required"] == "RETAKE"
    assert body["data"]["retake_reason"] == "wrong angle"
    assert body["data"]["image_url"] is None


def test_quality_analyze_external_timeout_returns_504(client, db_session, monkeypatch):
    procurement_item_id = _seed_procurement_item(db_session)

    class DummyClient:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def post(self, url, files):
            raise httpx.TimeoutException("timeout")

    monkeypatch.setattr(settings, "dl_quality_enabled", True)
    monkeypatch.setattr(settings, "dl_quality_api_url", "https://dl.example.com/analyze")
    monkeypatch.setattr(httpx, "Client", DummyClient)

    response = client.post(
        "/api/v1/owner/quality-inspections/analyze",
        headers=_owner_headers(),
        data={"procurement_item_id": str(procurement_item_id)},
        files={"image": ("apple.jpg", BytesIO(b"dl-image"), "image/jpeg")},
    )
    assert response.status_code == 504
    assert response.json()["message"] == "quality analysis timeout"


def test_quality_analyze_external_status_error_returns_502(client, db_session, monkeypatch):
    procurement_item_id = _seed_procurement_item(db_session)

    class DummyResponse:
        status_code = 500

        @staticmethod
        def json():
            return {"error": "dl failed"}

    class DummyClient:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def post(self, url, files):
            return DummyResponse()

    monkeypatch.setattr(settings, "dl_quality_enabled", True)
    monkeypatch.setattr(settings, "dl_quality_api_url", "https://dl.example.com/analyze")
    monkeypatch.setattr(httpx, "Client", DummyClient)

    response = client.post(
        "/api/v1/owner/quality-inspections/analyze",
        headers=_owner_headers(),
        data={"procurement_item_id": str(procurement_item_id)},
        files={"image": ("apple.jpg", BytesIO(b"dl-image"), "image/jpeg")},
    )
    assert response.status_code == 502
    assert response.json()["message"] == "failed to analyze quality image"


def test_quality_analyze_external_json_parse_failure_returns_502(client, db_session, monkeypatch):
    procurement_item_id = _seed_procurement_item(db_session)

    class DummyResponse:
        status_code = 200

        @staticmethod
        def json():
            raise ValueError("invalid json")

    class DummyClient:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def post(self, url, files):
            return DummyResponse()

    monkeypatch.setattr(settings, "dl_quality_enabled", True)
    monkeypatch.setattr(settings, "dl_quality_api_url", "https://dl.example.com/analyze")
    monkeypatch.setattr(httpx, "Client", DummyClient)

    response = client.post(
        "/api/v1/owner/quality-inspections/analyze",
        headers=_owner_headers(),
        data={"procurement_item_id": str(procurement_item_id)},
        files={"image": ("apple.jpg", BytesIO(b"dl-image"), "image/jpeg")},
    )
    assert response.status_code == 502
    assert response.json()["message"] == "invalid quality analysis response"


def test_quality_analyze_confidence_fallback_sets_retake(client, db_session, monkeypatch):
    procurement_item_id = _seed_procurement_item(db_session)

    class DummyResponse:
        status_code = 200

        @staticmethod
        def json():
            return {
                "data": {
                    "model_grade": "A",
                    "freshness_score": 90.0,
                    "color_score": 89.0,
                    "roundness_score": 88.0,
                    "bruise_probability": 0.04,
                    "angle_confidence": 0.42,
                    "grade_confidence": 0.90,
                    "model_version": "external-dl-v1",
                }
            }

    class DummyClient:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def post(self, url, files):
            return DummyResponse()

    monkeypatch.setattr(settings, "dl_quality_enabled", True)
    monkeypatch.setattr(settings, "dl_quality_api_url", "https://dl.example.com/analyze")
    monkeypatch.setattr(httpx, "Client", DummyClient)

    response = client.post(
        "/api/v1/owner/quality-inspections/analyze",
        headers=_owner_headers(),
        data={"procurement_item_id": str(procurement_item_id)},
        files={"image": ("apple.jpg", BytesIO(b"dl-image"), "image/jpeg")},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["data"]["action_required"] == "RETAKE"
    assert body["data"]["retake_reason"] == "low angle confidence"


def test_quality_analyze_confidence_fallback_sets_owner_review(client, db_session, monkeypatch):
    procurement_item_id = _seed_procurement_item(db_session)

    class DummyResponse:
        status_code = 200

        @staticmethod
        def json():
            return {
                "data": {
                    "model_grade": "A",
                    "freshness_score": 90.0,
                    "color_score": 89.0,
                    "roundness_score": 88.0,
                    "bruise_probability": 0.04,
                    "angle_confidence": 0.91,
                    "grade_confidence": 0.41,
                    "model_version": "external-dl-v1",
                }
            }

    class DummyClient:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def post(self, url, files):
            return DummyResponse()

    monkeypatch.setattr(settings, "dl_quality_enabled", True)
    monkeypatch.setattr(settings, "dl_quality_api_url", "https://dl.example.com/analyze")
    monkeypatch.setattr(httpx, "Client", DummyClient)

    response = client.post(
        "/api/v1/owner/quality-inspections/analyze",
        headers=_owner_headers(),
        data={"procurement_item_id": str(procurement_item_id)},
        files={"image": ("apple.jpg", BytesIO(b"dl-image"), "image/jpeg")},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["data"]["action_required"] == "OWNER_REVIEW"
    assert body["data"]["model_decision"] == "REVIEW"
