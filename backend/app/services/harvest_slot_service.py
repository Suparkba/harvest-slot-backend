from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from backend.app.core.status import HarvestSlotStatus
from backend.app.models.harvest_slot import HarvestSlot
from backend.app.repositories.farm_repo import FarmRepository
from backend.app.repositories.harvest_slot_repo import HarvestSlotRepository
from backend.app.repositories.product_repo import ProductRepository


def calculate_available_kg(slot: HarvestSlot) -> float:
    return float(slot.confirmed_reservable_kg) - float(slot.reserved_kg) - float(slot.sold_kg)


def serialize_slot(slot: HarvestSlot) -> dict:
    return {
        "slot_id": slot.slot_id,
        "farm_id": slot.farm_id,
        "farm_name": slot.farm.farm_name if slot.farm else None,
        "product_id": slot.product_id,
        "product_name": slot.product.product_name if slot.product else None,
        "image_url": slot.product.image_url if slot.product else None,
        "package_unit_kg": float(slot.product.package_unit_kg) if slot.product else None,
        "prediction_id": slot.prediction_id,
        "confirmed_harvest_start": slot.confirmed_harvest_start,
        "confirmed_harvest_end": slot.confirmed_harvest_end,
        "confirmed_reservable_kg": float(slot.confirmed_reservable_kg),
        "reserved_kg": float(slot.reserved_kg),
        "sold_kg": float(slot.sold_kg),
        "available_kg": calculate_available_kg(slot),
        "confirmed_price": slot.confirmed_price,
        "customer_notice": slot.customer_notice,
        "slot_status": slot.slot_status,
        "owner_confirmed_at": slot.owner_confirmed_at,
        "opened_at": slot.opened_at,
        "closed_at": slot.closed_at,
    }


class HarvestSlotService:
    def __init__(self, session: Session):
        self.session = session
        self.slot_repo = HarvestSlotRepository(session)
        self.farm_repo = FarmRepository(session)
        self.product_repo = ProductRepository(session)

    def list_product_slots(self, product_id: int) -> list[dict]:
        slots = self.slot_repo.list_by_product(product_id, only_open=True)
        return [serialize_slot(slot) for slot in slots]

    def list_owner_slots(self, owner_id: int) -> list[dict]:
        slots = (
            self.session.query(HarvestSlot)
            .join(HarvestSlot.farm)
            .filter(HarvestSlot.farm.has(owner_id=owner_id))
            .order_by(HarvestSlot.created_at.desc())
            .all()
        )
        return [serialize_slot(slot) for slot in slots]

    def create_slot(self, owner_id: int, payload: dict) -> dict:
        farm = self.farm_repo.get(payload["farm_id"])
        product = self.product_repo.get(payload["product_id"])
        if not farm or farm.owner_id != owner_id:
            raise HTTPException(status_code=404, detail="farm not found")
        if not product or product.farm_id != farm.farm_id:
            raise HTTPException(status_code=404, detail="product not found")
        now = datetime.utcnow()
        slot = HarvestSlot(**payload)
        if slot.slot_status in {HarvestSlotStatus.OPEN, HarvestSlotStatus.CLOSED}:
            slot.owner_confirmed_at = now
        if slot.slot_status == HarvestSlotStatus.OPEN:
            slot.opened_at = now
        if slot.slot_status == HarvestSlotStatus.CLOSED:
            slot.closed_at = now
        self.session.add(slot)
        self.session.commit()
        self.session.refresh(slot)
        return serialize_slot(slot)

    def update_slot(self, owner_id: int, slot_id: int, payload: dict) -> dict:
        slot = self.slot_repo.get(slot_id)
        if not slot or slot.farm.owner_id != owner_id:
            raise HTTPException(status_code=404, detail="slot not found")
        for key, value in payload.items():
            setattr(slot, key, value)
        self.session.commit()
        self.session.refresh(slot)
        return serialize_slot(slot)

    def update_slot_status(self, owner_id: int, slot_id: int, slot_status: str) -> dict:
        slot = self.slot_repo.get(slot_id)
        if not slot or slot.farm.owner_id != owner_id:
            raise HTTPException(status_code=404, detail="slot not found")
        now = datetime.utcnow()
        slot.slot_status = slot_status
        if slot_status == HarvestSlotStatus.OPEN:
            slot.owner_confirmed_at = slot.owner_confirmed_at or now
            slot.opened_at = now
        if slot_status == HarvestSlotStatus.CLOSED:
            slot.closed_at = now
        self.session.commit()
        self.session.refresh(slot)
        return serialize_slot(slot)
