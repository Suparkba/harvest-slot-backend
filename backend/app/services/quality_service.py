from datetime import datetime

from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.models.procurement import ProcurementItem
from backend.app.models.quality_inspection import QualityInspection
from backend.app.repositories.quality_repo import QualityRepository
from backend.app.services.quality_analysis_service import QualityAnalysisService
from backend.app.services.image_storage_service import ImageStorageService


def serialize_quality(inspection: QualityInspection) -> dict:
    return {
        "quality_inspection_id": inspection.quality_inspection_id,
        "procurement_item_id": inspection.procurement_item_id,
        "procurement_id": inspection.procurement_item.procurement_id if inspection.procurement_item else None,
        "procurement_no": (
            inspection.procurement_item.procurement.procurement_no
            if inspection.procurement_item and inspection.procurement_item.procurement
            else None
        ),
        "order_id": (
            inspection.procurement_item.procurement.order_id
            if inspection.procurement_item and inspection.procurement_item.procurement
            else None
        ),
        "order_no": (
            inspection.procurement_item.procurement.order.order_no
            if inspection.procurement_item and inspection.procurement_item.procurement and inspection.procurement_item.procurement.order
            else None
        ),
        "farm_name": (
            inspection.procurement_item.procurement.farm.farm_name
            if inspection.procurement_item and inspection.procurement_item.procurement and inspection.procurement_item.procurement.farm
            else None
        ),
        "product_id": (
            inspection.procurement_item.order_item.reservation_item.slot.product_id
            if inspection.procurement_item and inspection.procurement_item.order_item and inspection.procurement_item.order_item.reservation_item and inspection.procurement_item.order_item.reservation_item.slot
            else None
        ),
        "product_name": (
            inspection.procurement_item.order_item.reservation_item.slot.product.product_name
            if inspection.procurement_item and inspection.procurement_item.order_item and inspection.procurement_item.order_item.reservation_item and inspection.procurement_item.order_item.reservation_item.slot and inspection.procurement_item.order_item.reservation_item.slot.product
            else None
        ),
        "owner_id": inspection.owner_id,
        "image_url": inspection.image_url,
        "model_grade": inspection.model_grade,
        "freshness_score": float(inspection.freshness_score),
        "color_score": float(inspection.color_score),
        "roundness_score": float(inspection.roundness_score),
        "bruise_probability": float(inspection.bruise_probability),
        "model_decision": inspection.model_decision,
        "owner_confirmed_grade": inspection.owner_confirmed_grade,
        "owner_decision": inspection.owner_decision,
        "model_version": inspection.model_version,
        "inspected_at": inspection.inspected_at,
    }


class QualityService:
    def __init__(self, session: Session):
        self.session = session
        self.repo = QualityRepository(session)
        self.image_storage_service = ImageStorageService()
        self.quality_analysis_service = QualityAnalysisService()

    def _get_procurement_item(self, owner_id: int, procurement_item_id: int) -> ProcurementItem:
        procurement_item = self.session.get(ProcurementItem, procurement_item_id)
        if not procurement_item or procurement_item.procurement.owner_id != owner_id:
            raise HTTPException(status_code=404, detail="procurement item not found")
        return procurement_item

    def analyze_inspection_image(
        self,
        owner_id: int,
        procurement_item_id: int,
        *,
        image: UploadFile | None = None,
        image_url: str | None = None,
        persist_image: bool = False,
    ) -> dict:
        self._get_procurement_item(owner_id, procurement_item_id)

        persisted_image_url = image_url
        file_name = None
        subfolder = None

        if persist_image:
            if image is None:
                raise HTTPException(status_code=400, detail="image file required when persist_image is true")
            upload_result = self.image_storage_service.upload_image(
                image,
                product_seq=procurement_item_id,
                subfolder=f"{settings.image_default_quality_subfolder}/{owner_id}",
            )
            persisted_image_url = upload_result["file_url"]
            file_name = upload_result["file_name"]
            subfolder = upload_result["subfolder"]

        analysis = self.quality_analysis_service.analyze(
            image=image,
            image_url=persisted_image_url,
        )
        response = {
            "procurement_item_id": procurement_item_id,
            "image_persisted": persist_image,
            **analysis,
        }
        response["image_url"] = persisted_image_url
        if not persist_image and image is not None and image_url is None:
            response["image_url"] = None
        if file_name:
            response["file_name"] = file_name
        if subfolder:
            response["subfolder"] = subfolder
        return response

    def create_inspection(self, owner_id: int, payload: dict) -> dict:
        procurement_item = self._get_procurement_item(owner_id, payload["procurement_item_id"])
        analysis = self.quality_analysis_service.analyze(image_url=payload["image_url"])

        inspection = QualityInspection(
            procurement_item_id=procurement_item.procurement_item_id,
            owner_id=owner_id,
            image_url=payload["image_url"],
            model_grade=analysis["model_grade"],
            freshness_score=analysis["freshness_score"],
            color_score=analysis["color_score"],
            roundness_score=analysis["roundness_score"],
            bruise_probability=analysis["bruise_probability"],
            model_decision=analysis["model_decision"],
            owner_confirmed_grade=payload.get("owner_confirmed_grade"),
            owner_decision=payload.get("owner_decision"),
            model_version=analysis["model_version"],
            inspected_at=datetime.utcnow(),
        )
        self.session.add(inspection)
        self.session.commit()
        self.session.refresh(inspection)
        return serialize_quality(inspection)

    def list_inspections(self, owner_id: int) -> list[dict]:
        return [serialize_quality(row) for row in self.repo.list_by_owner(owner_id)]

    def upload_inspection_image(self, owner_id: int, upload: UploadFile) -> dict:
        upload_result = self.image_storage_service.upload_image(
            upload,
            product_seq=owner_id,
            subfolder=f"{settings.image_default_quality_subfolder}/{owner_id}",
        )
        return {
            "owner_id": owner_id,
            "image_url": upload_result["file_url"],
            "file_name": upload_result["file_name"],
            "subfolder": upload_result["subfolder"],
        }
