import pytest
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from backend.app.models.harvest_slot import HarvestSlot
from backend.app.models.reservation import Reservation
from backend.app.services.reservation_service import ReservationService
from backend.app.services.reservation_service import (
    calculate_available_kg,
    calculate_reserved_kg,
    ensure_quantity_available,
)


def test_calculate_available_kg():
    slot = HarvestSlot(
        confirmed_reservable_kg=100.0,
        reserved_kg=15.0,
        sold_kg=10.0,
        farm_id=1,
        product_id=1,
        confirmed_harvest_start=None,
        confirmed_harvest_end=None,
        confirmed_price=39000,
        customer_notice="notice",
    )
    assert calculate_available_kg(slot) == 75.0


def test_package_count_times_package_unit_kg():
    assert calculate_reserved_kg(3, 5.0) == 15.0


def test_exceeds_available_kg_raises():
    with pytest.raises(HTTPException):
        ensure_quantity_available(15.0, 10.0)


def test_create_reservation_commits_even_after_auth_lookup(db_session):
    db_session.execute(select(Reservation).where(Reservation.customer_id == 101))

    created = ReservationService(db_session).create_reservation(
        customer_id=101,
        items=[{"slot_id": 1, "package_count": 1}],
    )
    reservation_id = created["reservation_id"]

    verification_session = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=db_session.get_bind(),
        future=True,
    )()
    try:
        saved = verification_session.get(Reservation, reservation_id)
        assert saved is not None
        assert saved.customer_id == 101
        assert saved.reservation_status == "RESERVED"
    finally:
        verification_session.close()
