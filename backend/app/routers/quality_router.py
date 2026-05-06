from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.security import AuthenticatedUser, require_owner
from backend.app.schemas.common_schema import success_response
from backend.app.schemas.quality_schema import QualityInspectionCreateRequest
from backend.app.services.quality_service import QualityService


router = APIRouter()


@router.post("/owner/quality-inspections")
def create_quality_inspection(
    payload: QualityInspectionCreateRequest,
    current_user: AuthenticatedUser = Depends(require_owner),
    db: Session = Depends(get_db),
) -> dict:
    return success_response(QualityService(db).create_inspection(current_user.owner_id, payload.model_dump()))


@router.get("/owner/quality-inspections")
def list_quality_inspections(
    current_user: AuthenticatedUser = Depends(require_owner),
    db: Session = Depends(get_db),
) -> dict:
    return success_response(QualityService(db).list_inspections(current_user.owner_id))
