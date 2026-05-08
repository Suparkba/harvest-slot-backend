from fastapi import HTTPException
from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from backend.app.core.status import HarvestSlotStatus, OrderStatus, ProcurementStatus, ReturnStatus
from backend.app.models.account import OwnerProfile
from backend.app.models.harvest_slot import HarvestSlot
from backend.app.models.procurement import Procurement, ProcurementItem
from backend.app.models.quality_inspection import QualityInspection
from backend.app.models.return_refund import ReturnRequest
from backend.app.models.shipment import Shipment


class OwnerService:
    def __init__(self, session: Session):
        self.session = session

    def dashboard(self, owner_id: int) -> dict:
        profile = self.session.get(OwnerProfile, owner_id)
        open_slots = self.session.scalar(
            select(func.count(HarvestSlot.slot_id)).where(
                and_(HarvestSlot.slot_status == HarvestSlotStatus.OPEN, HarvestSlot.farm.has(owner_id=owner_id))
            )
        ) or 0
        new_procurements = self.session.scalar(
            select(func.count(Procurement.procurement_id)).where(
                Procurement.owner_id == owner_id,
                Procurement.procurement_status == ProcurementStatus.REQUESTED,
            )
        ) or 0
        quality_waiting = self.session.scalar(
            select(func.count(ProcurementItem.procurement_item_id))
            .join(ProcurementItem.procurement)
            .outerjoin(QualityInspection, QualityInspection.procurement_item_id == ProcurementItem.procurement_item_id)
            .where(Procurement.owner_id == owner_id, QualityInspection.quality_inspection_id.is_(None))
        ) or 0
        ready_to_ship = self.session.scalar(
            select(func.count(Procurement.procurement_id))
            .outerjoin(Shipment, Shipment.order_id == Procurement.order_id)
            .where(
                Procurement.owner_id == owner_id,
                Procurement.procurement_status.in_(
                    [ProcurementStatus.APPROVED, ProcurementStatus.PARTIAL_APPROVED]
                ),
                Shipment.shipment_id.is_(None),
            )
        ) or 0
        return_requests = len(
            [
                row
                for row in self.session.query(ReturnRequest).all()
                if row.order.procurement
                and row.order.procurement.owner_id == owner_id
                and row.return_status == ReturnStatus.REQUESTED
            ]
        )
        return {
            "owner_id": owner_id,
            "owner_name": profile.owner_name if profile else None,
            "open_slots": int(open_slots),
            "new_procurements": int(new_procurements),
            "quality_waiting": int(quality_waiting),
            "ready_to_ship": int(ready_to_ship),
            "return_requests": int(return_requests),
        }

    def get_profile(self, owner_id: int) -> dict:
        profile = self.session.get(OwnerProfile, owner_id)
        if not profile:
            raise HTTPException(status_code=404, detail="owner profile not found")
        return {
            "owner_id": profile.owner_id,
            "owner_name": profile.owner_name,
            "owner_phone": profile.owner_phone,
            "business_number": profile.business_number,
            "email": profile.account.email,
            "account_status": profile.account.status,
        }

    def update_profile(self, owner_id: int, payload: dict) -> dict:
        profile = self.session.get(OwnerProfile, owner_id)
        if not profile:
            raise HTTPException(status_code=404, detail="owner profile not found")
        for key, value in payload.items():
            setattr(profile, key, value)
        self.session.commit()
        self.session.refresh(profile)
        return self.get_profile(owner_id)
