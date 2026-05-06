from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.models import Base, TimestampMixin

if TYPE_CHECKING:
    from backend.app.models.payment import Payment
    from backend.app.models.procurement import Procurement, ProcurementItem
    from backend.app.models.reservation import Reservation, ReservationItem
    from backend.app.models.return_refund import ReturnRequest
    from backend.app.models.shipment import Shipment


class Order(Base, TimestampMixin):
    __tablename__ = "orders"

    order_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    reservation_id: Mapped[int] = mapped_column(
        ForeignKey("reservations.reservation_id"),
        nullable=False,
        unique=True,
    )
    order_no: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    order_status: Mapped[str] = mapped_column(String(30), nullable=False, default="PAYMENT_PENDING")
    total_amount: Mapped[int] = mapped_column(Integer, nullable=False)
    receiver_name: Mapped[str] = mapped_column(String(100), nullable=False)
    receiver_phone: Mapped[str] = mapped_column(String(30), nullable=False)
    shipping_address: Mapped[str] = mapped_column(String(500), nullable=False)
    delivery_memo: Mapped[str | None] = mapped_column(String(500), nullable=True)
    ordered_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    reservation: Mapped["Reservation"] = relationship(back_populates="order")
    order_items: Mapped[list["OrderItem"]] = relationship(back_populates="order")
    payments: Mapped[list["Payment"]] = relationship(back_populates="order")
    procurement: Mapped["Procurement | None"] = relationship(back_populates="order", uselist=False)
    shipment: Mapped["Shipment | None"] = relationship(back_populates="order", uselist=False)
    return_request: Mapped["ReturnRequest | None"] = relationship(back_populates="order", uselist=False)


class OrderItem(Base, TimestampMixin):
    __tablename__ = "order_items"

    order_item_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.order_id"), nullable=False, index=True)
    reservation_item_id: Mapped[int] = mapped_column(
        ForeignKey("reservation_items.reservation_item_id"),
        nullable=False,
        unique=True,
    )
    package_count: Mapped[int] = mapped_column(Integer, nullable=False)
    ordered_kg: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    unit_price: Mapped[int] = mapped_column(Integer, nullable=False)
    subtotal_amount: Mapped[int] = mapped_column(Integer, nullable=False)
    order_item_status: Mapped[str] = mapped_column(String(30), nullable=False, default="ORDERED")

    order: Mapped[Order] = relationship(back_populates="order_items")
    reservation_item: Mapped["ReservationItem"] = relationship(back_populates="order_item")
    procurement_item: Mapped["ProcurementItem | None"] = relationship(back_populates="order_item", uselist=False)
