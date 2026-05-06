from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.security import AuthenticatedUser, require_owner
from backend.app.schemas.common_schema import success_response
from backend.app.schemas.harvest_slot_schema import (
    HarvestSlotCreateRequest,
    HarvestSlotStatusUpdateRequest,
    HarvestSlotUpdateRequest,
)
from backend.app.services.harvest_slot_service import HarvestSlotService


router = APIRouter()


@router.get("/owner/harvest-slots")
def owner_slots(
    current_user: AuthenticatedUser = Depends(require_owner),
    db: Session = Depends(get_db),
) -> dict:
    return success_response(HarvestSlotService(db).list_owner_slots(current_user.owner_id))


@router.post("/owner/harvest-slots")
def create_slot(
    payload: HarvestSlotCreateRequest,
    current_user: AuthenticatedUser = Depends(require_owner),
    db: Session = Depends(get_db),
) -> dict:
    return success_response(HarvestSlotService(db).create_slot(current_user.owner_id, payload.model_dump()))


@router.put("/owner/harvest-slots/{slot_id}")
def update_slot(
    slot_id: int,
    payload: HarvestSlotUpdateRequest,
    current_user: AuthenticatedUser = Depends(require_owner),
    db: Session = Depends(get_db),
) -> dict:
    return success_response(HarvestSlotService(db).update_slot(current_user.owner_id, slot_id, payload.model_dump()))


@router.patch("/owner/harvest-slots/{slot_id}/status")
def update_slot_status(
    slot_id: int,
    payload: HarvestSlotStatusUpdateRequest,
    current_user: AuthenticatedUser = Depends(require_owner),
    db: Session = Depends(get_db),
) -> dict:
    return success_response(
        HarvestSlotService(db).update_slot_status(current_user.owner_id, slot_id, payload.slot_status)
    )
