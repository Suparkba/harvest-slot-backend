from datetime import datetime, timedelta

from fastapi import HTTPException
from sqlalchemy.orm import Session

from backend.app.core.status import OrderItemStatus, OrderStatus, PaymentMethod, PaymentStatus, ProcurementStatus
from backend.app.core.transaction import transaction_scope
from backend.app.models.order import OrderItem
from backend.app.models.payment import Payment
from backend.app.models.procurement import Procurement, ProcurementItem
from backend.app.repositories.order_repo import OrderRepository
from backend.app.repositories.payment_repo import PaymentRepository


class PaymentService:
    def __init__(self, session: Session):
        self.session = session
        self.order_repo = OrderRepository(session)
        self.payment_repo = PaymentRepository(session)

    def mock_approve(self, payload: dict) -> dict:
        with transaction_scope(self.session):
            # Mock 결제 승인:
            # 1. orders 행 잠금
            order = self.order_repo.lock_order(payload["order_id"])
            if not order:
                raise HTTPException(status_code=404, detail="order not found")

            # 2. idempotency_key 중복 확인
            existing_payment = self.payment_repo.get_by_idempotency_key(payload["idempotency_key"])
            if existing_payment:
                return {
                    "payment_id": existing_payment.payment_id,
                    "payment_status": existing_payment.payment_status,
                    "order_status": order.order_status,
                    "idempotency_key": existing_payment.idempotency_key,
                }

            now = datetime.utcnow()
            payment = Payment(
                order_id=order.order_id,
                payment_provider="MOCK",
                payment_method=PaymentMethod.MOCK_CARD,
                payment_status=PaymentStatus.APPROVED,
                requested_amount=order.total_amount,
                approved_amount=order.total_amount,
                mock_transaction_key=f"mock-tx-{order.order_id}-{int(now.timestamp())}",
                idempotency_key=payload["idempotency_key"],
                requested_at=now,
                approved_at=now,
            )
            # 3. payments 생성
            self.session.add(payment)

            # 4. orders.order_status = PAID
            order.order_status = OrderStatus.PAID
            # 5. paid_at 기록
            order.paid_at = now

            farm_id = None
            owner_id = None
            for order_item in order.order_items:
                slot = order_item.reservation_item.slot
                if farm_id is None:
                    farm_id = slot.farm_id
                    owner_id = slot.farm.owner_id
                # 6. harvest_slots.reserved_kg 감소
                slot.reserved_kg = round(float(slot.reserved_kg) - float(order_item.ordered_kg), 2)
                # 7. harvest_slots.sold_kg 증가
                slot.sold_kg = round(float(slot.sold_kg) + float(order_item.ordered_kg), 2)
                order_item.order_item_status = OrderItemStatus.PROCUREMENT_REQUESTED

            procurement = Procurement(
                order_id=order.order_id,
                farm_id=farm_id,
                owner_id=owner_id,
                procurement_no=f"PRC-{int(now.timestamp())}",
                procurement_status=ProcurementStatus.REQUESTED,
                requested_at=now,
                response_deadline_at=now + timedelta(days=1),
            )
            # 8. procurements 생성
            self.session.add(procurement)
            self.session.flush()

            # 9. procurement_items 생성
            for order_item in order.order_items:
                procurement_item = ProcurementItem(
                    procurement_id=procurement.procurement_id,
                    order_item_id=order_item.order_item_id,
                    requested_package_count=order_item.package_count,
                    requested_kg=order_item.ordered_kg,
                    approved_package_count=0,
                    approved_kg=0,
                    approval_status=ProcurementStatus.REQUESTED,
                )
                self.session.add(procurement_item)

            # 10. orders.order_status = PROCUREMENT_REQUESTED
            order.order_status = OrderStatus.PROCUREMENT_REQUESTED
            # 11. commit
            self.session.flush()
            self.session.refresh(payment)

        return {
            "payment_id": payment.payment_id,
            "payment_status": payment.payment_status,
            "approved_amount": payment.approved_amount,
            "order_status": order.order_status,
            "procurement_id": procurement.procurement_id,
        }

    def list_order_payments(self, customer_id: int, order_id: int) -> list[dict]:
        order = self.order_repo.get(order_id)
        if not order or order.reservation.customer_id != customer_id:
            raise HTTPException(status_code=404, detail="order not found")
        payments = self.payment_repo.list_by_order(order_id)
        return [
            {
                "payment_id": payment.payment_id,
                "payment_status": payment.payment_status,
                "requested_amount": payment.requested_amount,
                "approved_amount": payment.approved_amount,
                "idempotency_key": payment.idempotency_key,
            }
            for payment in payments
        ]
