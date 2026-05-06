from sqlalchemy import select

from backend.app.models.shipment import Shipment
from backend.app.repositories.base_repo import BaseRepository


class ShipmentRepository(BaseRepository):
    def get(self, shipment_id: int) -> Shipment | None:
        return self.session.get(Shipment, shipment_id)

    def get_by_order(self, order_id: int) -> Shipment | None:
        return self.session.scalar(select(Shipment).where(Shipment.order_id == order_id))
