from sqlalchemy import desc, select
from sqlalchemy.orm import joinedload

from backend.app.models.reservation import Reservation
from backend.app.repositories.base_repo import BaseRepository


class ReservationRepository(BaseRepository):
    def get(self, reservation_id: int) -> Reservation | None:
        return self.session.get(Reservation, reservation_id)

    def lock_reservation(self, reservation_id: int) -> Reservation | None:
        stmt = select(Reservation).where(Reservation.reservation_id == reservation_id).with_for_update()
        return self.session.scalar(stmt)

    def lock_reservation_for_customer(self, reservation_id: int, customer_id: int) -> Reservation | None:
        stmt = (
            select(Reservation)
            .where(
                Reservation.reservation_id == reservation_id,
                Reservation.customer_id == customer_id,
            )
            .options(joinedload(Reservation.reservation_items))
            .with_for_update()
        )
        return self.session.scalar(stmt)

    def list_for_customer(self, customer_id: int, statuses: tuple[str, ...]) -> list[Reservation]:
        stmt = (
            select(Reservation)
            .where(
                Reservation.customer_id == customer_id,
                Reservation.reservation_status.in_(statuses),
            )
            .options(joinedload(Reservation.reservation_items))
            .order_by(desc(Reservation.created_at), desc(Reservation.reservation_id))
        )
        return list(self.session.scalars(stmt).unique().all())
