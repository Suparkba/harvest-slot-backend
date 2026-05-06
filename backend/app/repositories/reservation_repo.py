from sqlalchemy import select

from backend.app.models.reservation import Reservation
from backend.app.repositories.base_repo import BaseRepository


class ReservationRepository(BaseRepository):
    def get(self, reservation_id: int) -> Reservation | None:
        return self.session.get(Reservation, reservation_id)

    def lock_reservation(self, reservation_id: int) -> Reservation | None:
        stmt = select(Reservation).where(Reservation.reservation_id == reservation_id).with_for_update()
        return self.session.scalar(stmt)
