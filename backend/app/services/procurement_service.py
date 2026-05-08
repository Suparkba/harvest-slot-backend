from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from backend.app.core.status import OrderItemStatus, OrderStatus, ProcurementStatus
from backend.app.core.transaction import transaction_scope
from backend.app.models.procurement import Procurement
from backend.app.repositories.procurement_repo import ProcurementRepository


def serialize_procurement(procurement: Procurement) -> dict:
    return {
        "procurement_id": procurement.procurement_id,
        "order_id": procurement.order_id,
        "order_no": procurement.order.order_no if procurement.order else None,
        "reservation_id": procurement.order.reservation_id if procurement.order else None,
        "reservation_no": procurement.order.reservation.reservation_no if procurement.order and procurement.order.reservation else None,
        "customer_id": procurement.order.reservation.customer_id if procurement.order and procurement.order.reservation else None,
        "customer_name": (
            procurement.order.reservation.customer.customer_name
            if procurement.order and procurement.order.reservation and procurement.order.reservation.customer
            else None
        ),
        "farm_id": procurement.farm_id,
        "farm_name": procurement.farm.farm_name if procurement.farm else None,
        "owner_id": procurement.owner_id,
        "procurement_no": procurement.procurement_no,
        "procurement_status": procurement.procurement_status,
        "order_status": procurement.order.order_status if procurement.order else None,
        "shipment_status": procurement.order.shipment.shipment_status if procurement.order and procurement.order.shipment else None,
        "return_status": procurement.order.return_request.return_status if procurement.order and procurement.order.return_request else None,
        "total_amount": procurement.order.total_amount if procurement.order else None,
        "requested_at": procurement.requested_at,
        "response_deadline_at": procurement.response_deadline_at,
        "decided_at": procurement.decided_at,
        "rejected_reason": procurement.rejected_reason,
        "items": [
            {
                "procurement_item_id": item.procurement_item_id,
                "order_item_id": item.order_item_id,
                "product_id": item.order_item.reservation_item.slot.product_id if item.order_item and item.order_item.reservation_item and item.order_item.reservation_item.slot else None,
                "product_name": (
                    item.order_item.reservation_item.slot.product.product_name
                    if item.order_item and item.order_item.reservation_item and item.order_item.reservation_item.slot and item.order_item.reservation_item.slot.product
                    else None
                ),
                "image_url": (
                    item.order_item.reservation_item.slot.product.image_url
                    if item.order_item and item.order_item.reservation_item and item.order_item.reservation_item.slot and item.order_item.reservation_item.slot.product
                    else None
                ),
                "requested_package_count": item.requested_package_count,
                "requested_kg": float(item.requested_kg),
                "approved_package_count": item.approved_package_count,
                "approved_kg": float(item.approved_kg),
                "approval_status": item.approval_status,
                "owner_memo": item.owner_memo,
            }
            for item in procurement.procurement_items
        ],
    }


class ProcurementService:
    def __init__(self, session: Session):
        self.session = session
        self.repo = ProcurementRepository(session)

    def list_by_owner(self, owner_id: int) -> list[dict]:
        return [serialize_procurement(row) for row in self.repo.list_by_owner(owner_id)]

    def get_detail(self, owner_id: int, procurement_id: int) -> dict:
        procurement = self.repo.get(procurement_id)
        if not procurement or procurement.owner_id != owner_id:
            raise HTTPException(status_code=404, detail="procurement not found")
        return serialize_procurement(procurement)

    def decide(self, owner_id: int, procurement_id: int, payload: dict) -> dict:
        with transaction_scope(self.session):
            # 발주 결정:
            # 1. procurements 행 잠금
            procurement = self.repo.lock_procurement(procurement_id)
            if not procurement or procurement.owner_id != owner_id:
                raise HTTPException(status_code=404, detail="procurement not found")

            decision = payload["decision"]
            items_by_id = {item["procurement_item_id"]: item for item in payload["items"]}

            # 2. procurement_items 승인 수량 갱신
            for item in procurement.procurement_items:
                request_item = items_by_id.get(item.procurement_item_id)
                if request_item:
                    item.approved_package_count = request_item["approved_package_count"]
                    item.approved_kg = request_item["approved_kg"]
                    item.owner_memo = request_item.get("owner_memo")
                item.approval_status = decision
                if decision == ProcurementStatus.APPROVED:
                    item.order_item.order_item_status = OrderItemStatus.APPROVED
                elif decision == ProcurementStatus.PARTIAL_APPROVED:
                    item.order_item.order_item_status = OrderItemStatus.PARTIAL_APPROVED
                else:
                    item.order_item.order_item_status = OrderItemStatus.REJECTED

            # 3. procurements 상태 갱신
            procurement.procurement_status = decision
            procurement.decided_at = datetime.utcnow()
            procurement.rejected_reason = payload.get("rejected_reason")

            # 4. orders 상태 갱신
            if decision == ProcurementStatus.APPROVED:
                procurement.order.order_status = OrderStatus.PROCUREMENT_APPROVED
            elif decision == ProcurementStatus.PARTIAL_APPROVED:
                procurement.order.order_status = OrderStatus.PROCUREMENT_PARTIAL_APPROVED
            else:
                procurement.order.order_status = OrderStatus.PROCUREMENT_REJECTED

            # 5. commit
            self.session.flush()
            self.session.refresh(procurement)

        return serialize_procurement(procurement)
