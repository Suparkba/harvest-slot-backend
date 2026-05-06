from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.schemas.common_schema import success_response
from backend.app.services.harvest_slot_service import HarvestSlotService
from backend.app.services.product_service import ProductService


router = APIRouter()


@router.get("/farms/{farm_id}")
def get_farm(farm_id: int, db: Session = Depends(get_db)) -> dict:
    return success_response(ProductService(db).get_farm(farm_id))


@router.get("/products")
def list_products(
    featured: bool | None = Query(default=None),
    fruit_type: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> dict:
    return success_response(ProductService(db).list_public_products(featured=featured, fruit_type=fruit_type))


@router.get("/products/{product_id}")
def get_product(product_id: int, db: Session = Depends(get_db)) -> dict:
    return success_response(ProductService(db).get_product_detail(product_id))


@router.get("/products/{product_id}/slots")
def get_product_slots(product_id: int, db: Session = Depends(get_db)) -> dict:
    return success_response(HarvestSlotService(db).list_product_slots(product_id))
