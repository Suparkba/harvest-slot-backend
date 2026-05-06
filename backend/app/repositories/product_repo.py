from sqlalchemy import and_, case, func, select

from backend.app.core.status import HarvestSlotStatus, ProductStatus
from backend.app.models.farm import Farm
from backend.app.models.harvest_slot import HarvestSlot
from backend.app.models.product import Product
from backend.app.repositories.base_repo import BaseRepository


class ProductRepository(BaseRepository):
    def get(self, product_id: int) -> Product | None:
        return self.session.get(Product, product_id)

    def list_public(self, featured: bool | None = None, fruit_type: str | None = None) -> list[Product]:
        open_slot_count = func.count(HarvestSlot.slot_id).filter(HarvestSlot.slot_status == HarvestSlotStatus.OPEN)
        stmt = (
            select(Product)
            .outerjoin(
                HarvestSlot,
                and_(HarvestSlot.product_id == Product.product_id, HarvestSlot.slot_status == HarvestSlotStatus.OPEN),
            )
            .where(Product.product_status == ProductStatus.ACTIVE)
            .group_by(Product.product_id)
            .order_by(case((open_slot_count > 0, 0), else_=1), Product.created_at.desc())
        )
        if fruit_type:
            stmt = stmt.where(Product.fruit_type == fruit_type)
        if featured:
            stmt = stmt.having(open_slot_count > 0)
        return list(self.session.scalars(stmt).all())

    def list_by_owner(self, owner_id: int) -> list[Product]:
        stmt = select(Product).join(Farm).where(Farm.owner_id == owner_id).order_by(Product.created_at.desc())
        return list(self.session.scalars(stmt).all())
