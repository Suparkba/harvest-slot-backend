from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.security import AuthenticatedUser, require_customer, require_owner
from backend.app.schemas.common_schema import success_response
from backend.app.schemas.return_schema import ReturnCreateRequest, ReturnDecisionRequest
from backend.app.services.return_service import ReturnService


router = APIRouter()


@router.post("/returns")
def create_return(
    payload: ReturnCreateRequest,
    current_user: AuthenticatedUser = Depends(require_customer),
    db: Session = Depends(get_db),
) -> dict:
    return success_response(ReturnService(db).create_return_request(current_user.customer_id, payload.model_dump()))


@router.get("/owner/returns")
def owner_returns(
    current_user: AuthenticatedUser = Depends(require_owner),
    db: Session = Depends(get_db),
) -> dict:
    return success_response(ReturnService(db).list_owner_returns(current_user.owner_id))


@router.patch("/owner/returns/{return_request_id}/decision")
def decide_return(
    return_request_id: int,
    payload: ReturnDecisionRequest,
    current_user: AuthenticatedUser = Depends(require_owner),
    db: Session = Depends(get_db),
) -> dict:
    return success_response(ReturnService(db).decide_return(current_user.owner_id, return_request_id, payload.model_dump()))


@router.get("/me/returns")
def my_returns(
    current_user: AuthenticatedUser = Depends(require_customer),
    db: Session = Depends(get_db),
) -> dict:
    return success_response(ReturnService(db).list_my_returns(current_user.customer_id))
