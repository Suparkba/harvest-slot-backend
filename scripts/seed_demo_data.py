from datetime import date, datetime, timedelta

from sqlalchemy import select, text
from sqlalchemy.exc import SQLAlchemyError

from backend.app import models  # noqa: F401
from backend.app.core.database import SessionLocal
from backend.app.core.security import hash_password
from backend.app.models.account import Account, CustomerProfile, EmailVerification, OwnerProfile
from backend.app.models.farm import Farm
from backend.app.models.harvest_slot import HarvestSlot
from backend.app.models.ml_prediction import MLPrediction
from backend.app.models.order import Order, OrderItem
from backend.app.models.payment import Payment
from backend.app.models.procurement import Procurement, ProcurementItem
from backend.app.models.product import Product
from backend.app.models.quality_inspection import QualityInspection
from backend.app.models.reservation import Reservation, ReservationItem
from backend.app.models.return_refund import Refund, ReturnRequest
from backend.app.models.shipment import Shipment
from backend.app.services.email_verification_service import EmailVerificationService


def upsert(session, model, lookup: dict, values: dict):
    instance = session.scalar(select(model).filter_by(**lookup))
    if instance is None:
        instance = model(**lookup, **values)
        session.add(instance)
    else:
        for key, value in values.items():
            setattr(instance, key, value)
    session.flush()
    return instance


def seed_accounts(session) -> tuple[CustomerProfile, OwnerProfile]:
    customer_account = upsert(
        session,
        Account,
        {"email": "customer@test.com"},
        {
            "password_hash": hash_password("demo1234!"),
            "role": "CUSTOMER",
            "status": "ACTIVE",
            "email_verified": True,
        },
    )
    owner_account = upsert(
        session,
        Account,
        {"email": "owner@test.com"},
        {
            "password_hash": hash_password("demo1234!"),
            "role": "OWNER",
            "status": "ACTIVE",
            "email_verified": True,
        },
    )

    customer_profile = upsert(
        session,
        CustomerProfile,
        {"account_id": customer_account.account_id},
        {
            "customer_name": "Test Customer",
            "customer_phone": "010-1111-2222",
            "default_receiver_name": "Test Customer",
            "default_receiver_phone": "010-1111-2222",
            "default_shipping_address": "Seoul Test Address 101",
            "marketing_agree": True,
        },
    )
    owner_profile = upsert(
        session,
        OwnerProfile,
        {"account_id": owner_account.account_id},
        {
            "owner_name": "Test Owner",
            "owner_phone": "010-3333-4444",
            "business_number": "123-45-67890",
        },
    )

    upsert(
        session,
        EmailVerification,
        {"email": customer_account.email, "purpose": "SIGNUP"},
        {
            "account_id": customer_account.account_id,
            "code_hash": EmailVerificationService.hash_code(customer_account.email, "SIGNUP", "123456"),
            "verified": True,
            "expires_at": datetime.utcnow() + timedelta(minutes=30),
            "verified_at": datetime.utcnow(),
            "attempt_count": 0,
        },
    )
    upsert(
        session,
        EmailVerification,
        {"email": owner_account.email, "purpose": "SIGNUP"},
        {
            "account_id": owner_account.account_id,
            "code_hash": EmailVerificationService.hash_code(owner_account.email, "SIGNUP", "654321"),
            "verified": True,
            "expires_at": datetime.utcnow() + timedelta(minutes=30),
            "verified_at": datetime.utcnow(),
            "attempt_count": 0,
        },
    )
    return customer_profile, owner_profile


def seed_catalog(session, owner_profile: OwnerProfile) -> dict[str, object]:
    farm_main = upsert(
        session,
        Farm,
        {"owner_id": owner_profile.owner_id, "farm_name": "Seed Main Farm"},
        {
            "farm_region": "Gyeongbuk",
            "farm_address": "Gyeongbuk Farm Road 10",
            "farm_image_url": "/mock/farms/main_farm.jpg",
            "farm_description": "Main farm for demo products",
            "delivery_policy": "Ships within 1 business day",
            "return_policy": "Return request within 24 hours after delivery",
        },
    )
    farm_orchard = upsert(
        session,
        Farm,
        {"owner_id": owner_profile.owner_id, "farm_name": "Seed Orchard Farm"},
        {
            "farm_region": "Jeonnam",
            "farm_address": "Jeonnam Orchard Road 22",
            "farm_image_url": "/mock/farms/orchard_farm.jpg",
            "farm_description": "Second farm for additional listings",
            "delivery_policy": "Morning harvest and same-day packing",
            "return_policy": "Contact owner before return shipment",
        },
    )

    products = {
        "apple_fuji": upsert(
            session,
            Product,
            {"farm_id": farm_main.farm_id, "product_name": "Seed Apple Fuji 5kg"},
            {
                "fruit_type": "APPLE",
                "variety": "Fuji",
                "package_unit_kg": 5.0,
                "base_price": 39000,
                "product_status": "ACTIVE",
                "image_url": "/mock/products/apple_fuji_5kg.jpg",
                "product_description": "Popular Fuji apple set for reservation testing",
            },
        ),
        "apple_gala": upsert(
            session,
            Product,
            {"farm_id": farm_main.farm_id, "product_name": "Seed Apple Gala 3kg"},
            {
                "fruit_type": "APPLE",
                "variety": "Gala",
                "package_unit_kg": 3.0,
                "base_price": 26000,
                "product_status": "ACTIVE",
                "image_url": "/mock/products/apple_gala_3kg.jpg",
                "product_description": "Smaller apple package for quick order tests",
            },
        ),
        "pear_shingo": upsert(
            session,
            Product,
            {"farm_id": farm_main.farm_id, "product_name": "Seed Pear Shingo 3kg"},
            {
                "fruit_type": "PEAR",
                "variety": "Shingo",
                "package_unit_kg": 3.0,
                "base_price": 28000,
                "product_status": "ACTIVE",
                "image_url": "/mock/products/pear_shingo_3kg.jpg",
                "product_description": "Pear package used for list and slot tests",
            },
        ),
        "grape_shine": upsert(
            session,
            Product,
            {"farm_id": farm_orchard.farm_id, "product_name": "Seed Shine Muscat 2kg"},
            {
                "fruit_type": "GRAPE",
                "variety": "Shine Muscat",
                "package_unit_kg": 2.0,
                "base_price": 32000,
                "product_status": "ACTIVE",
                "image_url": "/mock/products/shine_muscat_2kg.jpg",
                "product_description": "Premium grape package",
            },
        ),
        "peach_momo": upsert(
            session,
            Product,
            {"farm_id": farm_orchard.farm_id, "product_name": "Seed Peach Momo 4kg"},
            {
                "fruit_type": "PEACH",
                "variety": "Momo",
                "package_unit_kg": 4.0,
                "base_price": 34000,
                "product_status": "ACTIVE",
                "image_url": "/mock/products/peach_momo_4kg.jpg",
                "product_description": "Peach package for additional UI cards",
            },
        ),
    }

    prediction = upsert(
        session,
        MLPrediction,
        {
            "farm_id": farm_main.farm_id,
            "product_id": products["apple_fuji"].product_id,
            "model_version": "mock-ml-v1-seed",
        },
        {
            "created_by_owner_id": owner_profile.owner_id,
            "input_feature_json": {"past_yield_kg": 900, "avg_temperature": 23.5},
            "open_api_snapshot_json": {"mock": True},
            "predicted_harvest_start": date.today() + timedelta(days=15),
            "predicted_harvest_end": date.today() + timedelta(days=21),
            "estimated_yield_kg": 420.0,
            "suggested_reservable_min_kg": 260.0,
            "suggested_reservable_max_kg": 320.0,
            "recommended_price": 39000,
            "confidence": 0.78,
            "safety_factor": 0.70,
            "warning_message": "Mock prediction for local integration",
        },
    )

    slots = {
        "apple_fuji_open_1": upsert(
            session,
            HarvestSlot,
            {"product_id": products["apple_fuji"].product_id, "customer_notice": "Seed open slot apple 1"},
            {
                "farm_id": farm_main.farm_id,
                "prediction_id": prediction.prediction_id,
                "confirmed_harvest_start": date.today() + timedelta(days=15),
                "confirmed_harvest_end": date.today() + timedelta(days=21),
                "confirmed_reservable_kg": 300.0,
                "reserved_kg": 20.0,
                "sold_kg": 25.0,
                "confirmed_price": 39000,
                "slot_status": "OPEN",
                "owner_confirmed_at": datetime.utcnow(),
                "opened_at": datetime.utcnow(),
                "closed_at": None,
            },
        ),
        "apple_fuji_open_2": upsert(
            session,
            HarvestSlot,
            {"product_id": products["apple_fuji"].product_id, "customer_notice": "Seed open slot apple 2"},
            {
                "farm_id": farm_main.farm_id,
                "prediction_id": prediction.prediction_id,
                "confirmed_harvest_start": date.today() + timedelta(days=25),
                "confirmed_harvest_end": date.today() + timedelta(days=30),
                "confirmed_reservable_kg": 240.0,
                "reserved_kg": 0.0,
                "sold_kg": 10.0,
                "confirmed_price": 40000,
                "slot_status": "OPEN",
                "owner_confirmed_at": datetime.utcnow(),
                "opened_at": datetime.utcnow(),
                "closed_at": None,
            },
        ),
        "pear_open": upsert(
            session,
            HarvestSlot,
            {"product_id": products["pear_shingo"].product_id, "customer_notice": "Seed open slot pear"},
            {
                "farm_id": farm_main.farm_id,
                "prediction_id": None,
                "confirmed_harvest_start": date.today() + timedelta(days=8),
                "confirmed_harvest_end": date.today() + timedelta(days=10),
                "confirmed_reservable_kg": 180.0,
                "reserved_kg": 5.0,
                "sold_kg": 0.0,
                "confirmed_price": 28000,
                "slot_status": "OPEN",
                "owner_confirmed_at": datetime.utcnow(),
                "opened_at": datetime.utcnow(),
                "closed_at": None,
            },
        ),
        "grape_open": upsert(
            session,
            HarvestSlot,
            {"product_id": products["grape_shine"].product_id, "customer_notice": "Seed open slot grape"},
            {
                "farm_id": farm_orchard.farm_id,
                "prediction_id": None,
                "confirmed_harvest_start": date.today() + timedelta(days=12),
                "confirmed_harvest_end": date.today() + timedelta(days=18),
                "confirmed_reservable_kg": 100.0,
                "reserved_kg": 4.0,
                "sold_kg": 2.0,
                "confirmed_price": 32000,
                "slot_status": "OPEN",
                "owner_confirmed_at": datetime.utcnow(),
                "opened_at": datetime.utcnow(),
                "closed_at": None,
            },
        ),
        "peach_open": upsert(
            session,
            HarvestSlot,
            {"product_id": products["peach_momo"].product_id, "customer_notice": "Seed open slot peach"},
            {
                "farm_id": farm_orchard.farm_id,
                "prediction_id": None,
                "confirmed_harvest_start": date.today() + timedelta(days=20),
                "confirmed_harvest_end": date.today() + timedelta(days=24),
                "confirmed_reservable_kg": 160.0,
                "reserved_kg": 0.0,
                "sold_kg": 0.0,
                "confirmed_price": 34000,
                "slot_status": "OPEN",
                "owner_confirmed_at": datetime.utcnow(),
                "opened_at": datetime.utcnow(),
                "closed_at": None,
            },
        ),
    }

    return {
        "farms": {"main": farm_main, "orchard": farm_orchard},
        "products": products,
        "slots": slots,
    }


def seed_order_bundle(
    session,
    *,
    customer_profile: CustomerProfile,
    owner_profile: OwnerProfile,
    farm: Farm,
    slot: HarvestSlot,
    reservation_no: str,
    order_no: str,
    procurement_no: str,
    idempotency_key: str,
    tracking_no: str | None,
    return_no: str | None,
    order_status: str,
    reservation_status: str,
    payment_status: str,
    procurement_status: str,
    shipment_status: str | None,
    return_status: str | None,
    refund_status: str | None,
    requested_amount: int,
    approved_amount: int,
    requested_package_count: int,
    requested_kg: float,
    quality_image_url: str | None = None,
) -> dict[str, object]:
    now = datetime.utcnow()
    reservation = upsert(
        session,
        Reservation,
        {"reservation_no": reservation_no},
        {
            "customer_id": customer_profile.customer_id,
            "reservation_status": reservation_status,
            "reserved_until": now + timedelta(minutes=30),
            "total_reserved_kg": requested_kg,
            "total_amount": requested_amount,
        },
    )
    reservation_item = upsert(
        session,
        ReservationItem,
        {"reservation_id": reservation.reservation_id, "slot_id": slot.slot_id},
        {
            "package_count": requested_package_count,
            "reserved_kg": requested_kg,
            "unit_price_snapshot": int(slot.confirmed_price),
            "subtotal_amount": requested_amount,
            "created_at": now,
        },
    )
    order = upsert(
        session,
        Order,
        {"order_no": order_no},
        {
            "reservation_id": reservation.reservation_id,
            "order_status": order_status,
            "total_amount": requested_amount,
            "receiver_name": customer_profile.default_receiver_name or customer_profile.customer_name,
            "receiver_phone": customer_profile.default_receiver_phone or customer_profile.customer_phone,
            "shipping_address": customer_profile.default_shipping_address or "Seoul Test Address 101",
            "delivery_memo": "Call first",
            "ordered_at": now - timedelta(days=2),
            "paid_at": now - timedelta(days=2),
        },
    )
    reservation.reservation_status = reservation_status

    order_item = upsert(
        session,
        OrderItem,
        {"reservation_item_id": reservation_item.reservation_item_id},
        {
            "order_id": order.order_id,
            "package_count": requested_package_count,
            "ordered_kg": requested_kg,
            "unit_price": int(slot.confirmed_price),
            "subtotal_amount": requested_amount,
            "order_item_status": "DELIVERED" if order_status in {"DELIVERED", "REFUNDED"} else "PROCUREMENT_REQUESTED",
        },
    )

    payment = upsert(
        session,
        Payment,
        {"idempotency_key": idempotency_key},
        {
            "order_id": order.order_id,
            "payment_provider": "MOCK",
            "payment_method": "MOCK_CARD",
            "payment_status": payment_status,
            "requested_amount": requested_amount,
            "approved_amount": approved_amount,
            "mock_transaction_key": f"mock-{idempotency_key}",
            "requested_at": now - timedelta(days=2),
            "approved_at": now - timedelta(days=2),
        },
    )

    procurement = upsert(
        session,
        Procurement,
        {"procurement_no": procurement_no},
        {
            "order_id": order.order_id,
            "farm_id": farm.farm_id,
            "owner_id": owner_profile.owner_id,
            "procurement_status": procurement_status,
            "requested_at": now - timedelta(days=2),
            "response_deadline_at": now + timedelta(days=1),
            "decided_at": now - timedelta(days=1) if procurement_status != "REQUESTED" else None,
            "rejected_reason": None,
        },
    )

    procurement_item = upsert(
        session,
        ProcurementItem,
        {"order_item_id": order_item.order_item_id},
        {
            "procurement_id": procurement.procurement_id,
            "requested_package_count": requested_package_count,
            "requested_kg": requested_kg,
            "approved_package_count": requested_package_count if procurement_status != "REQUESTED" else 0,
            "approved_kg": requested_kg if procurement_status != "REQUESTED" else 0,
            "approval_status": procurement_status,
            "owner_memo": "Seed demo item",
        },
    )

    shipment = None
    if shipment_status:
        shipment = upsert(
            session,
            Shipment,
            {"order_id": order.order_id},
            {
                "carrier_name": "Mock Express",
                "tracking_no": tracking_no or f"TRACK-{order_no}",
                "shipped_package_count": requested_package_count,
                "shipped_kg": requested_kg,
                "shipment_status": shipment_status,
                "shipped_at": now - timedelta(days=1),
                "delivered_at": now if shipment_status == "DELIVERED" else None,
            },
        )

    quality = None
    if quality_image_url:
        quality = upsert(
            session,
            QualityInspection,
            {"procurement_item_id": procurement_item.procurement_item_id},
            {
                "owner_id": owner_profile.owner_id,
                "image_url": quality_image_url,
                "model_grade": "A",
                "freshness_score": 91.2,
                "color_score": 88.0,
                "roundness_score": 93.5,
                "bruise_probability": 0.06,
                "model_decision": "PASS",
                "owner_confirmed_grade": "A",
                "owner_decision": "PASS",
                "model_version": "mock-dl-v1",
                "inspected_at": now - timedelta(days=1),
            },
        )

    return_request = None
    refund = None
    if return_status and return_no:
        return_request = upsert(
            session,
            ReturnRequest,
            {"return_no": return_no},
            {
                "order_id": order.order_id,
                "return_status": return_status,
                "reason_code": "QUALITY_ISSUE",
                "reason_detail": "Seed return request",
                "evidence_image_url": "/mock/returns/seed_return.jpg",
                "requested_amount": approved_amount,
                "approved_amount": approved_amount if return_status == "REFUNDED" else 0,
                "decision_reason": "Seed refund completed" if return_status == "REFUNDED" else None,
                "requested_at": now - timedelta(hours=10),
                "decided_at": now - timedelta(hours=8) if return_status != "REQUESTED" else None,
            },
        )
        if refund_status:
            refund = upsert(
                session,
                Refund,
                {"return_request_id": return_request.return_request_id},
                {
                    "payment_id": payment.payment_id,
                    "refund_status": refund_status,
                    "requested_amount": approved_amount,
                    "refunded_amount": approved_amount,
                    "requested_at": now - timedelta(hours=8),
                    "completed_at": now - timedelta(hours=7) if refund_status == "COMPLETED" else None,
                    "failure_reason": None,
                },
            )

    return {
        "reservation": reservation,
        "order": order,
        "order_item": order_item,
        "payment": payment,
        "procurement": procurement,
        "procurement_item": procurement_item,
        "shipment": shipment,
        "quality": quality,
        "return_request": return_request,
        "refund": refund,
    }


def main() -> None:
    try:
        session = SessionLocal()
        session.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        print(f"DB connection failed. Check .env and MySQL status. error={exc}")
        return

    with session:
        customer_profile, owner_profile = seed_accounts(session)
        catalog = seed_catalog(session, owner_profile)
        farms = catalog["farms"]
        slots = catalog["slots"]

        seed_order_bundle(
            session,
            customer_profile=customer_profile,
            owner_profile=owner_profile,
            farm=farms["main"],
            slot=slots["apple_fuji_open_1"],
            reservation_no="RSV-SEED-PROC-001",
            order_no="ORD-SEED-PROC-001",
            procurement_no="PRC-SEED-PROC-001",
            idempotency_key="seed-payment-proc-001",
            tracking_no=None,
            return_no=None,
            order_status="PROCUREMENT_REQUESTED",
            reservation_status="ORDERED",
            payment_status="APPROVED",
            procurement_status="REQUESTED",
            shipment_status=None,
            return_status=None,
            refund_status=None,
            requested_amount=78000,
            approved_amount=78000,
            requested_package_count=2,
            requested_kg=10.0,
        )

        seed_order_bundle(
            session,
            customer_profile=customer_profile,
            owner_profile=owner_profile,
            farm=farms["main"],
            slot=slots["pear_open"],
            reservation_no="RSV-SEED-DELIV-001",
            order_no="ORD-SEED-DELIV-001",
            procurement_no="PRC-SEED-DELIV-001",
            idempotency_key="seed-payment-deliv-001",
            tracking_no="TRACK-SEED-DELIV-001",
            return_no=None,
            order_status="DELIVERED",
            reservation_status="ORDERED",
            payment_status="APPROVED",
            procurement_status="APPROVED",
            shipment_status="DELIVERED",
            return_status=None,
            refund_status=None,
            requested_amount=56000,
            approved_amount=56000,
            requested_package_count=2,
            requested_kg=6.0,
            quality_image_url="/mock/quality/seed_quality_pear.jpg",
        )

        seed_order_bundle(
            session,
            customer_profile=customer_profile,
            owner_profile=owner_profile,
            farm=farms["orchard"],
            slot=slots["grape_open"],
            reservation_no="RSV-SEED-REFUND-001",
            order_no="ORD-SEED-REFUND-001",
            procurement_no="PRC-SEED-REFUND-001",
            idempotency_key="seed-payment-refund-001",
            tracking_no="TRACK-SEED-REFUND-001",
            return_no="RET-SEED-REFUND-001",
            order_status="REFUNDED",
            reservation_status="ORDERED",
            payment_status="REFUNDED",
            procurement_status="APPROVED",
            shipment_status="DELIVERED",
            return_status="REFUNDED",
            refund_status="COMPLETED",
            requested_amount=64000,
            approved_amount=32000,
            requested_package_count=2,
            requested_kg=4.0,
            quality_image_url="/mock/quality/seed_quality_grape.jpg",
        )

        session.commit()
        print("Seed demo data completed successfully.")


if __name__ == "__main__":
    main()
