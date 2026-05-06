from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.models import Base, TimestampMixin

if TYPE_CHECKING:
    from backend.app.models.account import OwnerProfile
    from backend.app.models.harvest_slot import HarvestSlot
    from backend.app.models.ml_prediction import MLPrediction
    from backend.app.models.procurement import Procurement
    from backend.app.models.product import Product


class Farm(Base, TimestampMixin):
    __tablename__ = "farms"

    farm_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("owner_profiles.owner_id"), nullable=False, index=True)
    farm_name: Mapped[str] = mapped_column(String(150), nullable=False)
    farm_region: Mapped[str] = mapped_column(String(100), nullable=False)
    farm_address: Mapped[str] = mapped_column(String(500), nullable=False)
    farm_image_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    farm_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    delivery_policy: Mapped[str | None] = mapped_column(Text, nullable=True)
    return_policy: Mapped[str | None] = mapped_column(Text, nullable=True)

    owner: Mapped["OwnerProfile"] = relationship(back_populates="farms")
    products: Mapped[list["Product"]] = relationship(back_populates="farm")
    ml_predictions: Mapped[list["MLPrediction"]] = relationship(back_populates="farm")
    harvest_slots: Mapped[list["HarvestSlot"]] = relationship(back_populates="farm")
    procurements: Mapped[list["Procurement"]] = relationship(back_populates="farm")
