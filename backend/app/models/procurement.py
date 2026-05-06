from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.models import Base, TimestampMixin

if TYPE_CHECKING:
    from backend.app.models.account import OwnerProfile
    from backend.app.models.farm import Farm
    from backend.app.models.order import Order, OrderItem
    from backend.app.models.quality_inspection import QualityInspection


class Procurement(Base, TimestampMixin):
    __tablename__ = "procurements"

    procurement_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.order_id"), nullable=False, unique=True)
    farm_id: Mapped[int] = mapped_column(ForeignKey("farms.farm_id"), nullable=False, index=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("owner_profiles.owner_id"), nullable=False, index=True)
    procurement_no: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    procurement_status: Mapped[str] = mapped_column(String(30), nullable=False, default="REQUESTED")
    requested_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    response_deadline_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    rejected_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)

    order: Mapped["Order"] = relationship(back_populates="procurement")
    farm: Mapped["Farm"] = relationship(back_populates="procurements")
    owner: Mapped["OwnerProfile"] = relationship(back_populates="procurements")
    procurement_items: Mapped[list["ProcurementItem"]] = relationship(back_populates="procurement")


class ProcurementItem(Base, TimestampMixin):
    __tablename__ = "procurement_items"

    procurement_item_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    procurement_id: Mapped[int] = mapped_column(
        ForeignKey("procurements.procurement_id"),
        nullable=False,
        index=True,
    )
    order_item_id: Mapped[int] = mapped_column(
        ForeignKey("order_items.order_item_id"),
        nullable=False,
        unique=True,
    )
    requested_package_count: Mapped[int] = mapped_column(Integer, nullable=False)
    requested_kg: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    approved_package_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    approved_kg: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    approval_status: Mapped[str] = mapped_column(String(30), nullable=False, default="REQUESTED")
    owner_memo: Mapped[str | None] = mapped_column(String(500), nullable=True)

    procurement: Mapped[Procurement] = relationship(back_populates="procurement_items")
    order_item: Mapped["OrderItem"] = relationship(back_populates="procurement_item")
    quality_inspections: Mapped[list["QualityInspection"]] = relationship(back_populates="procurement_item")
