from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, Date, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.models import Base

if TYPE_CHECKING:
    from backend.app.models.account import OwnerProfile
    from backend.app.models.farm import Farm
    from backend.app.models.harvest_slot import HarvestSlot
    from backend.app.models.product import Product


class MLPrediction(Base):
    __tablename__ = "ml_predictions"

    prediction_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    farm_id: Mapped[int] = mapped_column(ForeignKey("farms.farm_id"), nullable=False, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.product_id"), nullable=False, index=True)
    created_by_owner_id: Mapped[int] = mapped_column(
        ForeignKey("owner_profiles.owner_id"),
        nullable=False,
        index=True,
    )
    input_feature_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    open_api_snapshot_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    predicted_harvest_start: Mapped[date] = mapped_column(Date, nullable=False)
    predicted_harvest_end: Mapped[date] = mapped_column(Date, nullable=False)
    estimated_yield_kg: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    suggested_reservable_min_kg: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    suggested_reservable_max_kg: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    recommended_price: Mapped[int] = mapped_column(Integer, nullable=False)
    confidence: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False)
    safety_factor: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False)
    warning_message: Mapped[str] = mapped_column(String(500), nullable=False)
    model_version: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    farm: Mapped["Farm"] = relationship(back_populates="ml_predictions")
    product: Mapped["Product"] = relationship(back_populates="ml_predictions")
    created_by_owner: Mapped["OwnerProfile"] = relationship(back_populates="ml_predictions")
    harvest_slots: Mapped[list["HarvestSlot"]] = relationship(back_populates="prediction")
