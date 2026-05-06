from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.models import Base, TimestampMixin

if TYPE_CHECKING:
    from backend.app.models.account import CustomerProfile
    from backend.app.models.harvest_slot import HarvestSlot
    from backend.app.models.order import Order, OrderItem


class Reservation(Base, TimestampMixin):
    __tablename__ = "reservations"

    reservation_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customer_profiles.customer_id"), nullable=False, index=True)
    reservation_no: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    reservation_status: Mapped[str] = mapped_column(String(30), nullable=False, default="RESERVED")
    reserved_until: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    total_reserved_kg: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    total_amount: Mapped[int] = mapped_column(Integer, nullable=False)

    customer: Mapped["CustomerProfile"] = relationship(back_populates="reservations")
    reservation_items: Mapped[list["ReservationItem"]] = relationship(back_populates="reservation")
    order: Mapped["Order | None"] = relationship(back_populates="reservation", uselist=False)


class ReservationItem(Base):
    __tablename__ = "reservation_items"

    reservation_item_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    reservation_id: Mapped[int] = mapped_column(ForeignKey("reservations.reservation_id"), nullable=False, index=True)
    slot_id: Mapped[int] = mapped_column(ForeignKey("harvest_slots.slot_id"), nullable=False, index=True)
    package_count: Mapped[int] = mapped_column(Integer, nullable=False)
    reserved_kg: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    unit_price_snapshot: Mapped[int] = mapped_column(Integer, nullable=False)
    subtotal_amount: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    reservation: Mapped[Reservation] = relationship(back_populates="reservation_items")
    slot: Mapped["HarvestSlot"] = relationship(back_populates="reservation_items")
    order_item: Mapped["OrderItem | None"] = relationship(back_populates="reservation_item", uselist=False)
