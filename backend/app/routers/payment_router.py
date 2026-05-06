from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.security import AuthenticatedUser, require_customer
from backend.app.schemas.common_schema import success_response
from backend.app.schemas.payment_schema import PaymentMockApproveRequest
from backend.app.services.payment_service import PaymentService


router = APIRouter()


@router.post("/payments/mock-approve")
def mock_approve(
    payload: PaymentMockApproveRequest,
    _: AuthenticatedUser = Depends(require_customer),
    db: Session = Depends(get_db),
) -> dict:
    return success_response(PaymentService(db).mock_approve(payload.model_dump()))


@router.get("/me/orders/{order_id}/payments")
def order_payments(
    order_id: int,
    current_user: AuthenticatedUser = Depends(require_customer),
    db: Session = Depends(get_db),
) -> dict:
    return success_response(PaymentService(db).list_order_payments(current_user.customer_id, order_id))
