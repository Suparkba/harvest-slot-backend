from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from backend.app.core.status import QualityModelDecision
from backend.app.models.procurement import ProcurementItem
from backend.app.models.quality_inspection import QualityInspection
from backend.app.repositories.quality_repo import QualityRepository


def serialize_quality(inspection: QualityInspection) -> dict:
    return {
        "quality_inspection_id": inspection.quality_inspection_id,
        "procurement_item_id": inspection.procurement_item_id,
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

    def create_inspection(self, owner_id: int, payload: dict) -> dict:
        procurement_item = self.session.get(ProcurementItem, payload["procurement_item_id"])
        if not procurement_item or procurement_item.procurement.owner_id != owner_id:
            raise HTTPException(status_code=404, detail="procurement item not found")

        inspection = QualityInspection(
            procurement_item_id=procurement_item.procurement_item_id,
            owner_id=owner_id,
            image_url=payload["image_url"],
            model_grade="A",
            freshness_score=91.2,
            color_score=88.0,
            roundness_score=93.5,
            bruise_probability=0.06,
            model_decision=QualityModelDecision.PASS,
            owner_confirmed_grade=payload.get("owner_confirmed_grade"),
            owner_decision=payload.get("owner_decision"),
            model_version="mock-dl-v1",
            inspected_at=datetime.utcnow(),
        )
        # TODO: replace with real DL freshness classifier when model artifacts are available.
        self.session.add(inspection)
        self.session.commit()
        self.session.refresh(inspection)
        return serialize_quality(inspection)

    def list_inspections(self, owner_id: int) -> list[dict]:
        return [serialize_quality(row) for row in self.repo.list_by_owner(owner_id)]
