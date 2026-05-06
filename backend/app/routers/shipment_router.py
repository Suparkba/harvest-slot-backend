from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.security import AuthenticatedUser, require_customer, require_owner
from backend.app.schemas.common_schema import success_response
from backend.app.schemas.shipment_schema import ShipmentCreateRequest, ShipmentStatusUpdateRequest
from backend.app.services.shipment_service import ShipmentService


router = APIRouter()


@router.post("/owner/shipments")
def create_shipment(
    payload: ShipmentCreateRequest,
    current_user: AuthenticatedUser = Depends(require_owner),
    db: Session = Depends(get_db),
) -> dict:
    return success_response(ShipmentService(db).create_shipment(current_user.owner_id, payload.model_dump()))


@router.patch("/owner/shipments/{shipment_id}/status")
def update_shipment_status(
    shipment_id: int,
    payload: ShipmentStatusUpdateRequest,
    current_user: AuthenticatedUser = Depends(require_owner),
    db: Session = Depends(get_db),
) -> dict:
    return success_response(
        ShipmentService(db).update_shipment_status(current_user.owner_id, shipment_id, payload.shipment_status)
    )


@router.get("/me/orders/{order_id}/shipment")
def get_my_shipment(
    order_id: int,
    current_user: AuthenticatedUser = Depends(require_customer),
    db: Session = Depends(get_db),
) -> dict:
    return success_response(ShipmentService(db).get_my_shipment(current_user.customer_id, order_id))
