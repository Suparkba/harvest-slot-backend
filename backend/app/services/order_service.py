from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from backend.app.core.status import OrderItemStatus, OrderStatus, ReservationStatus
from backend.app.core.transaction import transaction_scope
from backend.app.models.order import Order, OrderItem
from backend.app.models.reservation import Reservation, ReservationItem
from backend.app.repositories.order_repo import OrderRepository
from backend.app.repositories.reservation_repo import ReservationRepository


def serialize_order(order: Order) -> dict:
    return {
        "order_id": order.order_id,
        "reservation_id": order.reservation_id,
        "order_no": order.order_no,
        "order_status": order.order_status,
        "total_amount": order.total_amount,
        "receiver_name": order.receiver_name,
        "receiver_phone": order.receiver_phone,
        "shipping_address": order.shipping_address,
        "delivery_memo": order.delivery_memo,
        "ordered_at": order.ordered_at,
        "paid_at": order.paid_at,
        "order_items": [
            {
                "order_item_id": item.order_item_id,
                "reservation_item_id": item.reservation_item_id,
                "package_count": item.package_count,
                "ordered_kg": float(item.ordered_kg),
                "unit_price": item.unit_price,
                "subtotal_amount": item.subtotal_amount,
                "order_item_status": item.order_item_status,
            }
            for item in order.order_items
        ],
    }


class OrderService:
    def __init__(self, session: Session):
        self.session = session
        self.reservation_repo = ReservationRepository(session)
        self.order_repo = OrderRepository(session)

    def create_from_reservation(self, customer_id: int, payload: dict) -> dict:
        with transaction_scope(self.session):
            # 주문 생성:
            # 1. reservations 행 잠금
            reservation = self.reservation_repo.lock_reservation(payload["reservation_id"])
            if not reservation:
                raise HTTPException(status_code=404, detail="reservation not found")
            if reservation.customer_id != customer_id:
                raise HTTPException(status_code=403, detail="reservation access denied")
            # 2. reservation_status = RESERVED 검증
            if reservation.reservation_status != ReservationStatus.RESERVED:
                raise HTTPException(status_code=400, detail="reservation is not in RESERVED state")
            # 3. reserved_until > now 검증
            if reservation.reserved_until <= datetime.utcnow():
                raise HTTPException(status_code=400, detail="reservation expired")

            # 4. orders 생성
            order = Order(
                reservation_id=reservation.reservation_id,
                order_no=f"ORD-{int(datetime.utcnow().timestamp())}",
                order_status=OrderStatus.PAYMENT_PENDING,
                total_amount=reservation.total_amount,
                receiver_name=payload["receiver_name"],
                receiver_phone=payload["receiver_phone"],
                shipping_address=payload["shipping_address"],
                delivery_memo=payload.get("delivery_memo"),
                ordered_at=datetime.utcnow(),
            )
            self.session.add(order)
            self.session.flush()

            # 5. order_items 생성
            for item in reservation.reservation_items:
                order_item = OrderItem(
                    order_id=order.order_id,
                    reservation_item_id=item.reservation_item_id,
                    package_count=item.package_count,
                    ordered_kg=item.reserved_kg,
                    unit_price=item.unit_price_snapshot,
                    subtotal_amount=item.subtotal_amount,
                    order_item_status=OrderItemStatus.ORDERED,
                )
                self.session.add(order_item)

            # 6. reservations.status = ORDERED
            reservation.reservation_status = ReservationStatus.ORDERED
            # 7. commit
            self.session.flush()
            self.session.refresh(order)
        self.session.refresh(order)
        return serialize_order(order)

    def list_my_orders(self, customer_id: int) -> list[dict]:
        rows = (
            self.session.query(Order)
            .join(Order.reservation)
            .filter(Reservation.customer_id == customer_id)
            .order_by(Order.created_at.desc())
            .all()
        )
        return [serialize_order(row) for row in rows]

    def get_my_order_detail(self, customer_id: int, order_id: int) -> dict:
        order = self.order_repo.get(order_id)
        if not order or order.reservation.customer_id != customer_id:
            raise HTTPException(status_code=404, detail="order not found")
        data = serialize_order(order)
        data["payments"] = [
            {
                "payment_id": payment.payment_id,
                "payment_status": payment.payment_status,
                "approved_amount": payment.approved_amount,
                "idempotency_key": payment.idempotency_key,
            }
            for payment in order.payments
        ]
        data["procurement"] = (
            {
                "procurement_id": order.procurement.procurement_id,
                "procurement_no": order.procurement.procurement_no,
                "procurement_status": order.procurement.procurement_status,
            }
            if order.procurement
            else None
        )
        data["shipment"] = (
            {
                "shipment_id": order.shipment.shipment_id,
                "shipment_status": order.shipment.shipment_status,
                "tracking_no": order.shipment.tracking_no,
            }
            if order.shipment
            else None
        )
        data["return_request"] = (
            {
                "return_request_id": order.return_request.return_request_id,
                "return_status": order.return_request.return_status,
            }
            if order.return_request
            else None
        )
        return data

    def list_owner_orders(self, owner_id: int) -> list[dict]:
        rows = self.session.query(Order).distinct().order_by(Order.created_at.desc()).all()
        filtered = [row for row in rows if any(item.reservation_item.slot.farm.owner_id == owner_id for item in row.order_items)]
        return [serialize_order(row) for row in filtered]
