from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.models import Base, TimestampMixin

if TYPE_CHECKING:
    from backend.app.models.order import Order


class Shipment(Base, TimestampMixin):
    __tablename__ = "shipments"

    shipment_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.order_id"), nullable=False, unique=True)
    carrier_name: Mapped[str] = mapped_column(String(100), nullable=False)
    tracking_no: Mapped[str] = mapped_column(String(100), nullable=False)
    shipped_package_count: Mapped[int] = mapped_column(Integer, nullable=False)
    shipped_kg: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    shipment_status: Mapped[str] = mapped_column(String(30), nullable=False, default="READY")
    shipped_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    order: Mapped["Order"] = relationship(back_populates="shipment")
