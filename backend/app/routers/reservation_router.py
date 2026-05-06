from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.security import AuthenticatedUser, require_customer, require_owner
from backend.app.schemas.common_schema import success_response
from backend.app.schemas.reservation_schema import ReservationCreateRequest, ReservationPreviewRequest
from backend.app.services.reservation_service import ReservationService


router = APIRouter()


@router.post("/reservations/preview")
def reservation_preview(payload: ReservationPreviewRequest, db: Session = Depends(get_db)) -> dict:
    return success_response(ReservationService(db).preview(payload.model_dump()["items"]))


@router.post("/reservations")
def create_reservation(
    payload: ReservationCreateRequest,
    current_user: AuthenticatedUser = Depends(require_customer),
    db: Session = Depends(get_db),
) -> dict:
    return success_response(ReservationService(db).create_reservation(current_user.customer_id, payload.model_dump()["items"]))


@router.get("/me/reservations")
def my_reservations(
    current_user: AuthenticatedUser = Depends(require_customer),
    db: Session = Depends(get_db),
) -> dict:
    return success_response(ReservationService(db).list_my_reservations(current_user.customer_id))


@router.get("/owner/reservations")
def owner_reservations(
    current_user: AuthenticatedUser = Depends(require_owner),
    db: Session = Depends(get_db),
) -> dict:
    return success_response(ReservationService(db).list_owner_reservations(current_user.owner_id))
