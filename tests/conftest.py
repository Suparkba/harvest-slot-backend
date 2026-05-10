from datetime import date, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.core.database import get_db
from backend.app.core.config import settings
from backend.app.core.security import hash_password
from backend.app.main import app
from backend.app.models import Base
from backend.app.models.account import Account, CustomerProfile, OwnerProfile
from backend.app.models.farm import Farm
from backend.app.models.harvest_slot import HarvestSlot
from backend.app.models.product import Product


@pytest.fixture(autouse=True)
def isolate_external_quality_analysis(monkeypatch):
    monkeypatch.setenv("TESTING", "true")
    monkeypatch.setenv("DL_QUALITY_ENABLED", "false")
    monkeypatch.setenv("DL_QUALITY_API_URL", "")
    monkeypatch.setattr(settings, "testing", True)
    monkeypatch.setattr(settings, "dl_quality_enabled", False)
    monkeypatch.setattr(settings, "dl_quality_api_url", "")


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    testing_session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)
    Base.metadata.create_all(bind=engine)
    session = testing_session_local()

    customer = Account(
        account_id=1,
        email="customer@test.com",
        password_hash=hash_password("demo1234!"),
        role="CUSTOMER",
        status="ACTIVE",
        email_verified=True,
    )
    owner = Account(
        account_id=2,
        email="owner@test.com",
        password_hash=hash_password("demo1234!"),
        role="OWNER",
        status="ACTIVE",
        email_verified=True,
    )
    session.add_all([customer, owner])
    session.flush()

    customer_profile = CustomerProfile(
        customer_id=101,
        account_id=customer.account_id,
        customer_name="Test Customer",
        customer_phone="010-0000-0000",
    )
    owner_profile = OwnerProfile(
        owner_id=1,
        account_id=owner.account_id,
        owner_name="Test Owner",
        owner_phone="010-9999-9999",
    )
    session.add_all([customer_profile, owner_profile])
    session.flush()

    farm = Farm(
        farm_id=1,
        owner_id=owner_profile.owner_id,
        farm_name="Test Farm",
        farm_region="Seoul",
        farm_address="Test Address",
    )
    session.add(farm)
    session.flush()

    product = Product(
        product_id=1,
        farm_id=farm.farm_id,
        product_name="Test Apple Box",
        fruit_type="APPLE",
        variety="Fuji",
        package_unit_kg=5.0,
        base_price=39000,
        product_status="ACTIVE",
    )
    session.add(product)
    session.flush()

    open_slot = HarvestSlot(
        slot_id=1,
        farm_id=farm.farm_id,
        product_id=product.product_id,
        prediction_id=None,
        confirmed_harvest_start=date.today(),
        confirmed_harvest_end=date.today() + timedelta(days=5),
        confirmed_reservable_kg=100.0,
        reserved_kg=10.0,
        sold_kg=5.0,
        confirmed_price=39000,
        customer_notice="Test notice",
        slot_status="OPEN",
        owner_confirmed_at=datetime.utcnow(),
        opened_at=datetime.utcnow(),
    )
    session.add(open_slot)
    session.commit()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
