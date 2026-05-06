from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.security import AuthenticatedUser, require_owner
from backend.app.schemas.common_schema import success_response
from backend.app.schemas.procurement_schema import ProcurementDecisionRequest
from backend.app.services.procurement_service import ProcurementService


router = APIRouter()


@router.get("/owner/procurements")
def owner_procurements(
    current_user: AuthenticatedUser = Depends(require_owner),
    db: Session = Depends(get_db),
) -> dict:
    return success_response(ProcurementService(db).list_by_owner(current_user.owner_id))


@router.get("/owner/procurements/{procurement_id}")
def procurement_detail(
    procurement_id: int,
    current_user: AuthenticatedUser = Depends(require_owner),
    db: Session = Depends(get_db),
) -> dict:
    return success_response(ProcurementService(db).get_detail(current_user.owner_id, procurement_id))


@router.patch("/owner/procurements/{procurement_id}/decision")
def procurement_decision(
    procurement_id: int,
    payload: ProcurementDecisionRequest,
    current_user: AuthenticatedUser = Depends(require_owner),
    db: Session = Depends(get_db),
) -> dict:
    return success_response(ProcurementService(db).decide(current_user.owner_id, procurement_id, payload.model_dump()))
