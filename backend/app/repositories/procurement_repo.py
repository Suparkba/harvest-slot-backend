from sqlalchemy import select

from backend.app.models.procurement import Procurement
from backend.app.repositories.base_repo import BaseRepository


class ProcurementRepository(BaseRepository):
    def get(self, procurement_id: int) -> Procurement | None:
        return self.session.get(Procurement, procurement_id)

    def list_by_owner(self, owner_id: int) -> list[Procurement]:
        stmt = select(Procurement).where(Procurement.owner_id == owner_id).order_by(Procurement.created_at.desc())
        return list(self.session.scalars(stmt).all())

    def lock_procurement(self, procurement_id: int) -> Procurement | None:
        stmt = select(Procurement).where(Procurement.procurement_id == procurement_id).with_for_update()
        return self.session.scalar(stmt)
