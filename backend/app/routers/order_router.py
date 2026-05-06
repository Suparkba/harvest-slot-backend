from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.security import AuthenticatedUser, require_customer, require_owner
from backend.app.schemas.common_schema import success_response
from backend.app.schemas.order_schema import OrderFromReservationRequest
from backend.app.services.order_service import OrderService


router = APIRouter()


@router.post("/orders/from-reservation")
def create_order(
    payload: OrderFromReservationRequest,
    current_user: AuthenticatedUser = Depends(require_customer),
    db: Session = Depends(get_db),
) -> dict:
    return success_response(OrderService(db).create_from_reservation(current_user.customer_id, payload.model_dump()))


@router.get("/me/orders")
def my_orders(
    current_user: AuthenticatedUser = Depends(require_customer),
    db: Session = Depends(get_db),
) -> dict:
    return success_response(OrderService(db).list_my_orders(current_user.customer_id))


@router.get("/me/orders/{order_id}")
def my_order_detail(
    order_id: int,
    current_user: AuthenticatedUser = Depends(require_customer),
    db: Session = Depends(get_db),
) -> dict:
    return success_response(OrderService(db).get_my_order_detail(current_user.customer_id, order_id))


@router.get("/owner/orders")
def owner_orders(
    current_user: AuthenticatedUser = Depends(require_owner),
    db: Session = Depends(get_db),
) -> dict:
    return success_response(OrderService(db).list_owner_orders(current_user.owner_id))
