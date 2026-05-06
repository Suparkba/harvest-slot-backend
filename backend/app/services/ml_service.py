from datetime import date, timedelta

from fastapi import HTTPException
from sqlalchemy.orm import Session

from backend.app.models.ml_prediction import MLPrediction
from backend.app.repositories.farm_repo import FarmRepository
from backend.app.repositories.product_repo import ProductRepository


def serialize_prediction(prediction: MLPrediction) -> dict:
    return {
        "prediction_id": prediction.prediction_id,
        "farm_id": prediction.farm_id,
        "product_id": prediction.product_id,
        "predicted_harvest_start": prediction.predicted_harvest_start,
        "predicted_harvest_end": prediction.predicted_harvest_end,
        "estimated_yield_kg": float(prediction.estimated_yield_kg),
        "suggested_reservable_min_kg": float(prediction.suggested_reservable_min_kg),
        "suggested_reservable_max_kg": float(prediction.suggested_reservable_max_kg),
        "recommended_price": prediction.recommended_price,
        "confidence": float(prediction.confidence),
        "safety_factor": float(prediction.safety_factor),
        "warning_message": prediction.warning_message,
        "model_version": prediction.model_version,
    }


class MLService:
    def __init__(self, session: Session):
        self.session = session
        self.farm_repo = FarmRepository(session)
        self.product_repo = ProductRepository(session)

    def create_prediction(self, owner_id: int, payload: dict) -> dict:
        farm = self.farm_repo.get(payload["farm_id"])
        product = self.product_repo.get(payload["product_id"])
        if not farm or farm.owner_id != owner_id:
            raise HTTPException(status_code=404, detail="farm not found")
        if not product or product.farm_id != farm.farm_id:
            raise HTTPException(status_code=404, detail="product not found")

        features = payload["features"]
        base_yield = float(features.get("past_yield_kg", 400))
        estimated_yield_kg = round(base_yield * 0.47, 2)
        start = date.today() + timedelta(days=30)
        end = start + timedelta(days=6)

        prediction = MLPrediction(
            farm_id=farm.farm_id,
            product_id=product.product_id,
            created_by_owner_id=owner_id,
            input_feature_json=features,
            open_api_snapshot_json={"mock": True},
            predicted_harvest_start=start,
            predicted_harvest_end=end,
            estimated_yield_kg=estimated_yield_kg,
            suggested_reservable_min_kg=round(estimated_yield_kg * 0.62, 2),
            suggested_reservable_max_kg=round(estimated_yield_kg * 0.76, 2),
            recommended_price=int(features.get("suggested_price", product.base_price)),
            confidence=0.78,
            safety_factor=0.70,
            warning_message="기상과 생육 상황에 따라 점주 확정값을 조정하세요.",
            model_version="mock-ml-v1",
        )
        # TODO: replace with real ML model inference when model artifacts are available.
        self.session.add(prediction)
        self.session.commit()
        self.session.refresh(prediction)
        return serialize_prediction(prediction)

    def list_predictions(self, owner_id: int) -> list[dict]:
        rows = (
            self.session.query(MLPrediction)
            .filter(MLPrediction.created_by_owner_id == owner_id)
            .order_by(MLPrediction.created_at.desc())
            .all()
        )
        return [serialize_prediction(row) for row in rows]

    def get_prediction(self, owner_id: int, prediction_id: int) -> dict:
        prediction = self.session.get(MLPrediction, prediction_id)
        if not prediction or prediction.created_by_owner_id != owner_id:
            raise HTTPException(status_code=404, detail="prediction not found")
        return serialize_prediction(prediction)
