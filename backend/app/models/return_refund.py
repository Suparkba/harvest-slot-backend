from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.models import Base, TimestampMixin

if TYPE_CHECKING:
    from backend.app.models.order import Order
    from backend.app.models.payment import Payment


class ReturnRequest(Base, TimestampMixin):
    __tablename__ = "return_requests"

    return_request_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.order_id"), nullable=False, unique=True)
    return_no: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    return_status: Mapped[str] = mapped_column(String(30), nullable=False, default="REQUESTED")
    reason_code: Mapped[str] = mapped_column(String(100), nullable=False)
    reason_detail: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    evidence_image_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    requested_amount: Mapped[int] = mapped_column(Integer, nullable=False)
    approved_amount: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    decision_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    requested_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    order: Mapped["Order"] = relationship(back_populates="return_request")
    refund: Mapped["Refund | None"] = relationship(back_populates="return_request", uselist=False)


class Refund(Base, TimestampMixin):
    __tablename__ = "refunds"

    refund_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    return_request_id: Mapped[int] = mapped_column(
        ForeignKey("return_requests.return_request_id"),
        nullable=False,
        unique=True,
    )
    payment_id: Mapped[int] = mapped_column(ForeignKey("payments.payment_id"), nullable=False, unique=True)
    refund_status: Mapped[str] = mapped_column(String(30), nullable=False, default="REQUESTED")
    requested_amount: Mapped[int] = mapped_column(Integer, nullable=False)
    refunded_amount: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    requested_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)

    return_request: Mapped[ReturnRequest] = relationship(back_populates="refund")
    payment: Mapped["Payment"] = relationship(back_populates="refund")
