from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.core.database import Base


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )


from backend.app.models.account import Account, CustomerProfile, EmailVerification, OwnerProfile
from backend.app.models.farm import Farm
from backend.app.models.harvest_slot import HarvestSlot
from backend.app.models.ml_prediction import MLPrediction
from backend.app.models.order import Order, OrderItem
from backend.app.models.payment import Payment
from backend.app.models.procurement import Procurement, ProcurementItem
from backend.app.models.product import Product
from backend.app.models.quality_inspection import QualityInspection
from backend.app.models.reservation import Reservation, ReservationItem
from backend.app.models.return_refund import Refund, ReturnRequest
from backend.app.models.shipment import Shipment

__all__ = [
    "Base",
    "TimestampMixin",
    "Account",
    "CustomerProfile",
    "OwnerProfile",
    "EmailVerification",
    "Farm",
    "Product",
    "MLPrediction",
    "HarvestSlot",
    "Reservation",
    "ReservationItem",
    "Order",
    "OrderItem",
    "Payment",
    "Procurement",
    "ProcurementItem",
    "QualityInspection",
    "Shipment",
    "ReturnRequest",
    "Refund",
]
