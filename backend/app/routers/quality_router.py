from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
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


@router.post("/owner/quality-inspections/analyze")
async def analyze_quality_inspection_image(
    request: Request,
    procurement_item_id: int | None = Form(default=None, description="Procurement item id"),
    image: UploadFile | None = File(default=None, description="Quality analysis image file"),
    image_url: str | None = Form(default=None, description="Existing image URL"),
    persist_image: bool = Form(default=False, description="Persist image to NAS when true"),
    current_user: AuthenticatedUser = Depends(require_owner),
    db: Session = Depends(get_db),
) -> dict:
    payload_procurement_item_id = procurement_item_id
    payload_image_url = image_url
    payload_persist_image = persist_image
    payload_image = image

    content_type = request.headers.get("content-type", "").split(";")[0].strip().lower()
    if content_type == "application/json":
        body = await request.json()
        payload_procurement_item_id = body.get("procurement_item_id")
        payload_image_url = body.get("image_url")
        payload_persist_image = body.get("persist_image", False)
        payload_image = None

    if payload_procurement_item_id is None:
        raise HTTPException(status_code=400, detail="procurement item not found")
    if payload_image is None and not payload_image_url:
        raise HTTPException(status_code=400, detail="image or image_url required")

    data = QualityService(db).analyze_inspection_image(
        current_user.owner_id,
        int(payload_procurement_item_id),
        image=payload_image,
        image_url=payload_image_url,
        persist_image=bool(payload_persist_image),
    )
    return success_response(data, message="quality analysis completed")


@router.post("/owner/quality-inspections/image")
def upload_quality_inspection_image(
    file: UploadFile = File(..., description="Quality inspection image file"),
    current_user: AuthenticatedUser = Depends(require_owner),
    db: Session = Depends(get_db),
) -> dict:
    return success_response(QualityService(db).upload_inspection_image(current_user.owner_id, file))


@router.get("/owner/quality-inspections")
def list_quality_inspections(
    current_user: AuthenticatedUser = Depends(require_owner),
    db: Session = Depends(get_db),
) -> dict:
    return success_response(QualityService(db).list_inspections(current_user.owner_id))
