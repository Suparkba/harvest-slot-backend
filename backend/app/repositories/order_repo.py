from sqlalchemy import select

from backend.app.models.order import Order
from backend.app.repositories.base_repo import BaseRepository


class OrderRepository(BaseRepository):
    def get(self, order_id: int) -> Order | None:
        return self.session.get(Order, order_id)

    def lock_order(self, order_id: int) -> Order | None:
        stmt = select(Order).where(Order.order_id == order_id).with_for_update()
        return self.session.scalar(stmt)
