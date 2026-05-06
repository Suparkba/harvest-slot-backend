from sqlalchemy import desc, select

from backend.app.models.payment import Payment
from backend.app.repositories.base_repo import BaseRepository


class PaymentRepository(BaseRepository):
    def get_by_idempotency_key(self, idempotency_key: str) -> Payment | None:
        return self.session.scalar(select(Payment).where(Payment.idempotency_key == idempotency_key))

    def list_by_order(self, order_id: int) -> list[Payment]:
        stmt = select(Payment).where(Payment.order_id == order_id).order_by(desc(Payment.created_at))
        return list(self.session.scalars(stmt).all())
