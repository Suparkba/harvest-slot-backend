from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.models import Base, TimestampMixin

if TYPE_CHECKING:
    from backend.app.models.farm import Farm
    from backend.app.models.harvest_slot import HarvestSlot
    from backend.app.models.ml_prediction import MLPrediction


class Product(Base, TimestampMixin):
    __tablename__ = "products"

    product_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    farm_id: Mapped[int] = mapped_column(ForeignKey("farms.farm_id"), nullable=False, index=True)
    product_name: Mapped[str] = mapped_column(String(200), nullable=False)
    fruit_type: Mapped[str] = mapped_column(String(50), nullable=False)
    variety: Mapped[str] = mapped_column(String(100), nullable=False)
    package_unit_kg: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    base_price: Mapped[int] = mapped_column(Integer, nullable=False)
    product_status: Mapped[str] = mapped_column(String(20), nullable=False, default="ACTIVE")
    image_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    product_description: Mapped[str | None] = mapped_column(Text, nullable=True)

    farm: Mapped["Farm"] = relationship(back_populates="products")
    ml_predictions: Mapped[list["MLPrediction"]] = relationship(back_populates="product")
    harvest_slots: Mapped[list["HarvestSlot"]] = relationship(back_populates="product")
