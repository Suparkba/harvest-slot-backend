from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.security import AuthenticatedUser, require_owner
from backend.app.schemas.common_schema import success_response
from backend.app.schemas.owner_schema import OwnerProfileUpdateRequest
from backend.app.schemas.product_schema import (
    FarmUpdateRequest,
    ProductCreateRequest,
    ProductStatusUpdateRequest,
    ProductUpdateRequest,
)
from backend.app.services.owner_service import OwnerService
from backend.app.services.product_service import ProductService


router = APIRouter()


@router.get("/owner/dashboard")
def owner_dashboard(
    current_user: AuthenticatedUser = Depends(require_owner),
    db: Session = Depends(get_db),
) -> dict:
    return success_response(OwnerService(db).dashboard(current_user.owner_id))


@router.get("/owner/farms/me")
def owner_farms(
    current_user: AuthenticatedUser = Depends(require_owner),
    db: Session = Depends(get_db),
) -> dict:
    return success_response(ProductService(db).get_owner_farms(current_user.owner_id))


@router.put("/owner/farms/{farm_id}")
def update_farm(
    farm_id: int,
    payload: FarmUpdateRequest,
    current_user: AuthenticatedUser = Depends(require_owner),
    db: Session = Depends(get_db),
) -> dict:
    return success_response(ProductService(db).update_farm(current_user.owner_id, farm_id, payload.model_dump()))


@router.get("/owner/products")
def owner_products(
    current_user: AuthenticatedUser = Depends(require_owner),
    db: Session = Depends(get_db),
) -> dict:
    return success_response(ProductService(db).list_owner_products(current_user.owner_id))


@router.post("/owner/products")
def create_product(
    payload: ProductCreateRequest,
    current_user: AuthenticatedUser = Depends(require_owner),
    db: Session = Depends(get_db),
) -> dict:
    return success_response(ProductService(db).create_product(current_user.owner_id, payload.model_dump()))


@router.put("/owner/products/{product_id}")
def update_product(
    product_id: int,
    payload: ProductUpdateRequest,
    current_user: AuthenticatedUser = Depends(require_owner),
    db: Session = Depends(get_db),
) -> dict:
    return success_response(ProductService(db).update_product(current_user.owner_id, product_id, payload.model_dump()))


@router.patch("/owner/products/{product_id}/status")
def update_product_status(
    product_id: int,
    payload: ProductStatusUpdateRequest,
    current_user: AuthenticatedUser = Depends(require_owner),
    db: Session = Depends(get_db),
) -> dict:
    return success_response(
        ProductService(db).update_product_status(current_user.owner_id, product_id, payload.product_status)
    )


@router.get("/owner/profile")
def owner_profile(
    current_user: AuthenticatedUser = Depends(require_owner),
    db: Session = Depends(get_db),
) -> dict:
    return success_response(OwnerService(db).get_profile(current_user.owner_id))


@router.put("/owner/profile")
def update_owner_profile(
    payload: OwnerProfileUpdateRequest,
    current_user: AuthenticatedUser = Depends(require_owner),
    db: Session = Depends(get_db),
) -> dict:
    return success_response(OwnerService(db).update_profile(current_user.owner_id, payload.model_dump()))
