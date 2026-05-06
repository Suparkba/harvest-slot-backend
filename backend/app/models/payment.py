from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.models import Base, TimestampMixin

if TYPE_CHECKING:
    from backend.app.models.order import Order
    from backend.app.models.return_refund import Refund


class Payment(Base, TimestampMixin):
    __tablename__ = "payments"

    payment_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.order_id"), nullable=False, index=True)
    payment_provider: Mapped[str] = mapped_column(String(30), nullable=False, default="MOCK")
    payment_method: Mapped[str] = mapped_column(String(30), nullable=False, default="MOCK_CARD")
    payment_status: Mapped[str] = mapped_column(String(30), nullable=False, default="REQUESTED")
    requested_amount: Mapped[int] = mapped_column(Integer, nullable=False)
    approved_amount: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    mock_transaction_key: Mapped[str | None] = mapped_column(String(200), nullable=True)
    idempotency_key: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    requested_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    failed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)

    order: Mapped["Order"] = relationship(back_populates="payments")
    refund: Mapped["Refund | None"] = relationship(back_populates="payment", uselist=False)
