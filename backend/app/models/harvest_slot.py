from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.models import Base, TimestampMixin

if TYPE_CHECKING:
    from backend.app.models.farm import Farm
    from backend.app.models.ml_prediction import MLPrediction
    from backend.app.models.product import Product
    from backend.app.models.reservation import ReservationItem


class HarvestSlot(Base, TimestampMixin):
    __tablename__ = "harvest_slots"

    slot_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    farm_id: Mapped[int] = mapped_column(ForeignKey("farms.farm_id"), nullable=False, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.product_id"), nullable=False, index=True)
    prediction_id: Mapped[int | None] = mapped_column(
        ForeignKey("ml_predictions.prediction_id"),
        nullable=True,
        index=True,
    )
    confirmed_harvest_start: Mapped[date] = mapped_column(Date, nullable=False)
    confirmed_harvest_end: Mapped[date] = mapped_column(Date, nullable=False)
    confirmed_reservable_kg: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    reserved_kg: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    sold_kg: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    confirmed_price: Mapped[int] = mapped_column(Integer, nullable=False)
    customer_notice: Mapped[str] = mapped_column(String(500), nullable=False)
    slot_status: Mapped[str] = mapped_column(String(20), nullable=False, default="DRAFT")
    owner_confirmed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    opened_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    farm: Mapped["Farm"] = relationship(back_populates="harvest_slots")
    product: Mapped["Product"] = relationship(back_populates="harvest_slots")
    prediction: Mapped["MLPrediction | None"] = relationship(back_populates="harvest_slots")
    reservation_items: Mapped[list["ReservationItem"]] = relationship(back_populates="slot")
