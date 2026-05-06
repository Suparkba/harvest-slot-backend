from datetime import date, datetime, timedelta

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from backend.app import models  # noqa: F401
from backend.app.core.security import hash_password
from backend.app.core.database import SessionLocal
from backend.app.models.account import Account, CustomerProfile, EmailVerification, OwnerProfile
from backend.app.models.farm import Farm
from backend.app.models.harvest_slot import HarvestSlot
from backend.app.models.ml_prediction import MLPrediction
from backend.app.models.order import Order, OrderItem
from backend.app.models.payment import Payment
from backend.app.models.procurement import Procurement, ProcurementItem
from backend.app.models.product import Product
from backend.app.models.reservation import Reservation, ReservationItem
from backend.app.models.return_refund import Refund, ReturnRequest
from backend.app.models.shipment import Shipment


def main() -> None:
    try:
        session = SessionLocal()
        session.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        print(f"DB 연결에 실패했습니다. .env 설정과 MySQL 상태를 확인해주세요. error={exc}")
        return

    with session:
        customer_account = Account(
            email="customer@test.com",
            password_hash=hash_password("demo1234!"),
            role="CUSTOMER",
            status="ACTIVE",
            email_verified=True,
        )
        owner_account = Account(
            email="owner@test.com",
            password_hash=hash_password("demo1234!"),
            role="OWNER",
            status="ACTIVE",
            email_verified=True,
        )
        session.add_all([customer_account, owner_account])
        session.flush()

        customer_profile = CustomerProfile(
            account_id=customer_account.account_id,
            customer_name="데모 고객",
            customer_phone="010-1111-2222",
            default_receiver_name="데모 고객",
            default_receiver_phone="010-1111-2222",
            default_shipping_address="서울시 강남구 데모로 1",
        )
        owner_profile = OwnerProfile(
            account_id=owner_account.account_id,
            owner_name="데모 점주",
            owner_phone="010-3333-4444",
            business_number="123-45-67890",
        )
        session.add_all([customer_profile, owner_profile])
        session.flush()

        session.add_all(
            [
                EmailVerification(
                    account_id=customer_account.account_id,
                    email=customer_account.email,
                    purpose="SIGNUP",
                    verification_code="123456",
                    verified=True,
                    expires_at=datetime.utcnow() + timedelta(minutes=30),
                    verified_at=datetime.utcnow(),
                ),
                EmailVerification(
                    account_id=owner_account.account_id,
                    email=owner_account.email,
                    purpose="SIGNUP",
                    verification_code="654321",
                    verified=True,
                    expires_at=datetime.utcnow() + timedelta(minutes=30),
                    verified_at=datetime.utcnow(),
                ),
            ]
        )

        farm = Farm(
            owner_id=owner_profile.owner_id,
            farm_name="Harvest Demo Farm",
            farm_region="경북",
            farm_address="경북 데모시 농장길 10",
            farm_description="데모 농장입니다.",
            delivery_policy="평일 출고",
            return_policy="배송 완료 후 24시간 내 접수",
        )
        session.add(farm)
        session.flush()

        product1 = Product(
            farm_id=farm.farm_id,
            product_name="예약 사과 5kg",
            fruit_type="APPLE",
            variety="Fuji",
            package_unit_kg=5.0,
            base_price=39000,
            product_status="ACTIVE",
        )
        product2 = Product(
            farm_id=farm.farm_id,
            product_name="예약 배 3kg",
            fruit_type="PEAR",
            variety="Shingo",
            package_unit_kg=3.0,
            base_price=28000,
            product_status="ACTIVE",
        )
        session.add_all([product1, product2])
        session.flush()

        prediction = MLPrediction(
            farm_id=farm.farm_id,
            product_id=product1.product_id,
            created_by_owner_id=owner_profile.owner_id,
            input_feature_json={"past_yield_kg": 900},
            open_api_snapshot_json={"mock": True},
            predicted_harvest_start=date.today() + timedelta(days=30),
            predicted_harvest_end=date.today() + timedelta(days=36),
            estimated_yield_kg=420.0,
            suggested_reservable_min_kg=260.0,
            suggested_reservable_max_kg=320.0,
            recommended_price=39000,
            confidence=0.78,
            safety_factor=0.70,
            warning_message="기상과 생육 상황에 따라 점주 확정값을 조정하세요.",
            model_version="mock-ml-v1",
        )
        session.add(prediction)
        session.flush()

        open_slot = HarvestSlot(
            farm_id=farm.farm_id,
            product_id=product1.product_id,
            prediction_id=prediction.prediction_id,
            confirmed_harvest_start=prediction.predicted_harvest_start,
            confirmed_harvest_end=prediction.predicted_harvest_end,
            confirmed_reservable_kg=300.0,
            reserved_kg=10.0,
            sold_kg=0.0,
            confirmed_price=39000,
            customer_notice="수확 예정 범위는 기상 상황에 따라 조정될 수 있습니다.",
            slot_status="OPEN",
            owner_confirmed_at=datetime.utcnow(),
            opened_at=datetime.utcnow(),
        )
        closed_slot = HarvestSlot(
            farm_id=farm.farm_id,
            product_id=product2.product_id,
            prediction_id=None,
            confirmed_harvest_start=date.today() + timedelta(days=10),
            confirmed_harvest_end=date.today() + timedelta(days=12),
            confirmed_reservable_kg=120.0,
            reserved_kg=0.0,
            sold_kg=0.0,
            confirmed_price=28000,
            customer_notice="마감된 테스트 슬롯입니다.",
            slot_status="CLOSED",
            owner_confirmed_at=datetime.utcnow(),
            closed_at=datetime.utcnow(),
        )
        session.add_all([open_slot, closed_slot])
        session.flush()

        reservation = Reservation(
            customer_id=customer_profile.customer_id,
            reservation_no="RSV-DEMO-001",
            reservation_status="ORDERED",
            reserved_until=datetime.utcnow() + timedelta(minutes=20),
            total_reserved_kg=10.0,
            total_amount=78000,
        )
        session.add(reservation)
        session.flush()

        reservation_item = ReservationItem(
            reservation_id=reservation.reservation_id,
            slot_id=open_slot.slot_id,
            package_count=2,
            reserved_kg=10.0,
            unit_price_snapshot=39000,
            subtotal_amount=78000,
        )
        session.add(reservation_item)
        session.flush()

        order = Order(
            reservation_id=reservation.reservation_id,
            order_no="ORD-DEMO-001",
            order_status="DELIVERED",
            total_amount=78000,
            receiver_name="데모 고객",
            receiver_phone="010-1111-2222",
            shipping_address="서울시 강남구 데모로 1",
            delivery_memo="문 앞에 놓아주세요",
            ordered_at=datetime.utcnow() - timedelta(days=2),
            paid_at=datetime.utcnow() - timedelta(days=2),
        )
        session.add(order)
        session.flush()

        order_item = OrderItem(
            order_id=order.order_id,
            reservation_item_id=reservation_item.reservation_item_id,
            package_count=2,
            ordered_kg=10.0,
            unit_price=39000,
            subtotal_amount=78000,
            order_item_status="DELIVERED",
        )
        session.add(order_item)
        session.flush()

        payment = Payment(
            order_id=order.order_id,
            payment_provider="MOCK",
            payment_method="MOCK_CARD",
            payment_status="APPROVED",
            requested_amount=78000,
            approved_amount=78000,
            mock_transaction_key="mock-demo-payment",
            idempotency_key="demo-payment-001",
            requested_at=datetime.utcnow() - timedelta(days=2),
            approved_at=datetime.utcnow() - timedelta(days=2),
        )
        session.add(payment)
        session.flush()

        procurement = Procurement(
            order_id=order.order_id,
            farm_id=farm.farm_id,
            owner_id=owner_profile.owner_id,
            procurement_no="PRC-DEMO-001",
            procurement_status="APPROVED",
            requested_at=datetime.utcnow() - timedelta(days=2),
            decided_at=datetime.utcnow() - timedelta(days=2),
        )
        session.add(procurement)
        session.flush()

        procurement_item = ProcurementItem(
            procurement_id=procurement.procurement_id,
            order_item_id=order_item.order_item_id,
            requested_package_count=2,
            requested_kg=10.0,
            approved_package_count=2,
            approved_kg=10.0,
            approval_status="APPROVED",
            owner_memo="정상 승인",
        )
        session.add(procurement_item)
        session.flush()

        shipment = Shipment(
            order_id=order.order_id,
            carrier_name="Mock Express",
            tracking_no="TRACK-DEMO-001",
            shipped_package_count=2,
            shipped_kg=10.0,
            shipment_status="DELIVERED",
            shipped_at=datetime.utcnow() - timedelta(days=1),
            delivered_at=datetime.utcnow(),
        )
        session.add(shipment)
        session.flush()

        return_request = ReturnRequest(
            order_id=order.order_id,
            return_no="RET-DEMO-001",
            return_status="REFUNDED",
            reason_code="DAMAGED",
            reason_detail="테스트용 반품",
            requested_amount=39000,
            approved_amount=39000,
            decision_reason="테스트 승인",
            requested_at=datetime.utcnow() - timedelta(hours=10),
            decided_at=datetime.utcnow() - timedelta(hours=8),
        )
        session.add(return_request)
        session.flush()

        refund = Refund(
            return_request_id=return_request.return_request_id,
            payment_id=payment.payment_id,
            refund_status="COMPLETED",
            requested_amount=39000,
            refunded_amount=39000,
            requested_at=datetime.utcnow() - timedelta(hours=8),
            completed_at=datetime.utcnow() - timedelta(hours=7),
        )
        session.add(refund)

        session.commit()
        print("데모 시드 데이터 생성이 완료되었습니다.")


if __name__ == "__main__":
    main()
