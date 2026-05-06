from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from backend.app.core.status import OrderStatus, ShipmentStatus
from backend.app.models.shipment import Shipment
from backend.app.repositories.order_repo import OrderRepository
from backend.app.repositories.shipment_repo import ShipmentRepository


def serialize_shipment(shipment: Shipment) -> dict:
    return {
        "shipment_id": shipment.shipment_id,
        "order_id": shipment.order_id,
        "carrier_name": shipment.carrier_name,
        "tracking_no": shipment.tracking_no,
        "shipped_package_count": shipment.shipped_package_count,
        "shipped_kg": float(shipment.shipped_kg),
        "shipment_status": shipment.shipment_status,
        "shipped_at": shipment.shipped_at,
        "delivered_at": shipment.delivered_at,
    }


class ShipmentService:
    def __init__(self, session: Session):
        self.session = session
        self.order_repo = OrderRepository(session)
        self.shipment_repo = ShipmentRepository(session)

    def create_shipment(self, owner_id: int, payload: dict) -> dict:
        order = self.order_repo.get(payload["order_id"])
        if not order or not order.procurement or order.procurement.owner_id != owner_id:
            raise HTTPException(status_code=404, detail="order not found")
        if order.shipment:
            raise HTTPException(status_code=400, detail="shipment already exists for order")

        shipment = Shipment(
            order_id=order.order_id,
            carrier_name=payload["carrier_name"],
            tracking_no=payload["tracking_no"],
            shipped_package_count=payload["shipped_package_count"],
            shipped_kg=payload["shipped_kg"],
            shipment_status=ShipmentStatus.SHIPPED,
            shipped_at=datetime.utcnow(),
        )
        self.session.add(shipment)
        order.order_status = OrderStatus.SHIPPED
        self.session.commit()
        self.session.refresh(shipment)
        return serialize_shipment(shipment)

    def update_shipment_status(self, owner_id: int, shipment_id: int, shipment_status: str) -> dict:
        shipment = self.shipment_repo.get(shipment_id)
        if not shipment or not shipment.order.procurement or shipment.order.procurement.owner_id != owner_id:
            raise HTTPException(status_code=404, detail="shipment not found")
        shipment.shipment_status = shipment_status
        if shipment_status == ShipmentStatus.SHIPPED and not shipment.shipped_at:
            shipment.shipped_at = datetime.utcnow()
            shipment.order.order_status = OrderStatus.SHIPPED
        if shipment_status == ShipmentStatus.DELIVERED:
            shipment.delivered_at = datetime.utcnow()
            shipment.order.order_status = OrderStatus.DELIVERED
        self.session.commit()
        self.session.refresh(shipment)
        return serialize_shipment(shipment)

    def get_my_shipment(self, customer_id: int, order_id: int) -> dict:
        shipment = self.shipment_repo.get_by_order(order_id)
        if not shipment or shipment.order.reservation.customer_id != customer_id:
            raise HTTPException(status_code=404, detail="shipment not found")
        return serialize_shipment(shipment)
