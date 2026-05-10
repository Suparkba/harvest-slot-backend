from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.models import Base, TimestampMixin

if TYPE_CHECKING:
    from backend.app.models.farm import Farm
    from backend.app.models.ml_prediction import MLPrediction
    from backend.app.models.procurement import Procurement
    from backend.app.models.quality_inspection import QualityInspection
    from backend.app.models.reservation import Reservation


class Account(Base, TimestampMixin):
    __tablename__ = "accounts"

    account_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="ACTIVE")
    email_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    customer_profile: Mapped[CustomerProfile | None] = relationship(back_populates="account", uselist=False)
    owner_profile: Mapped[OwnerProfile | None] = relationship(back_populates="account", uselist=False)
    email_verifications: Mapped[list[EmailVerification]] = relationship(back_populates="account")


class CustomerProfile(Base, TimestampMixin):
    __tablename__ = "customer_profiles"

    customer_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.account_id"), unique=True, nullable=False)
    customer_name: Mapped[str] = mapped_column(String(100), nullable=False)
    customer_phone: Mapped[str] = mapped_column(String(30), nullable=False)
    default_receiver_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    default_receiver_phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    default_shipping_address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    marketing_agree: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    account: Mapped[Account] = relationship(back_populates="customer_profile")
    reservations: Mapped[list["Reservation"]] = relationship(back_populates="customer")


class OwnerProfile(Base, TimestampMixin):
    __tablename__ = "owner_profiles"

    owner_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.account_id"), unique=True, nullable=False)
    owner_name: Mapped[str] = mapped_column(String(100), nullable=False)
    owner_phone: Mapped[str] = mapped_column(String(30), nullable=False)
    business_number: Mapped[str | None] = mapped_column(String(50), nullable=True)

    account: Mapped[Account] = relationship(back_populates="owner_profile")
    farms: Mapped[list["Farm"]] = relationship(back_populates="owner")
    ml_predictions: Mapped[list["MLPrediction"]] = relationship(back_populates="created_by_owner")
    procurements: Mapped[list["Procurement"]] = relationship(back_populates="owner")
    quality_inspections: Mapped[list["QualityInspection"]] = relationship(back_populates="owner")


class EmailVerification(Base, TimestampMixin):
    __tablename__ = "email_verifications"

    email_verification_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    account_id: Mapped[int | None] = mapped_column(ForeignKey("accounts.account_id"), nullable=True, index=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    purpose: Mapped[str] = mapped_column(String(30), nullable=False)
    code_hash: Mapped[str] = mapped_column("verification_code", String(255), nullable=False)
    verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default=text("0"))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    account: Mapped[Account | None] = relationship(back_populates="email_verifications")
