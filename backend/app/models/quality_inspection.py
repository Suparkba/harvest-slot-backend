from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.models import Base

if TYPE_CHECKING:
    from backend.app.models.account import OwnerProfile
    from backend.app.models.procurement import ProcurementItem


class QualityInspection(Base):
    __tablename__ = "quality_inspections"

    quality_inspection_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    procurement_item_id: Mapped[int] = mapped_column(
        ForeignKey("procurement_items.procurement_item_id"),
        nullable=False,
        index=True,
    )
    owner_id: Mapped[int] = mapped_column(ForeignKey("owner_profiles.owner_id"), nullable=False, index=True)
    image_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    model_grade: Mapped[str] = mapped_column(String(20), nullable=False)
    freshness_score: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    color_score: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    roundness_score: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    bruise_probability: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False)
    model_decision: Mapped[str] = mapped_column(String(20), nullable=False)
    owner_confirmed_grade: Mapped[str | None] = mapped_column(String(20), nullable=True)
    owner_decision: Mapped[str | None] = mapped_column(String(20), nullable=True)
    model_version: Mapped[str] = mapped_column(String(50), nullable=False)
    inspected_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    procurement_item: Mapped["ProcurementItem"] = relationship(back_populates="quality_inspections")
    owner: Mapped["OwnerProfile"] = relationship(back_populates="quality_inspections")
