from sqlalchemy import select

from backend.app.models.harvest_slot import HarvestSlot
from backend.app.repositories.base_repo import BaseRepository


class HarvestSlotRepository(BaseRepository):
    def get(self, slot_id: int) -> HarvestSlot | None:
        return self.session.get(HarvestSlot, slot_id)

    def list_by_product(self, product_id: int, only_open: bool = False) -> list[HarvestSlot]:
        stmt = select(HarvestSlot).where(HarvestSlot.product_id == product_id).order_by(HarvestSlot.created_at.desc())
        if only_open:
            stmt = stmt.where(HarvestSlot.slot_status == "OPEN")
        return list(self.session.scalars(stmt).all())

    def list_by_owner(self, owner_id: int) -> list[HarvestSlot]:
        stmt = (
            select(HarvestSlot)
            .join(HarvestSlot.farm)
            .where(HarvestSlot.farm.has(owner_id=owner_id))
            .order_by(HarvestSlot.created_at.desc())
        )
        return list(self.session.scalars(stmt).all())

    def lock_slots(self, slot_ids: list[int]) -> list[HarvestSlot]:
        stmt = select(HarvestSlot).where(HarvestSlot.slot_id.in_(slot_ids)).with_for_update()
        return list(self.session.scalars(stmt).all())
