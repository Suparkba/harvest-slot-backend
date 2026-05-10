from datetime import date, timedelta
from pathlib import Path
from typing import Any

import joblib
import pandas as pd
from fastapi import HTTPException
from sqlalchemy.orm import Session

from backend.app.models.ml_prediction import MLPrediction
from backend.app.repositories.farm_repo import FarmRepository
from backend.app.repositories.product_repo import ProductRepository

FEATURES = [
    "mar_avg_temp",
    "aug_sunshine",
    "oct_rainfall",
    "aug_humidity",
]

MODEL_VERSION = "rf-apple-harvest-v1"
MODEL_PATH = Path(__file__).resolve().parent.parent / "ml_models" / "model.joblib"
APPLE_VARIETY_FUJI = "\ubd80\uc0ac"
NORMAL_WARNING_MESSAGE = "\uc815\uc0c1"
_MODEL = None


def get_model() -> Any:
    global _MODEL
    if _MODEL is not None:
        return _MODEL
    if not MODEL_PATH.exists():
        raise HTTPException(status_code=500, detail="ML model is not available")
    try:
        _MODEL = joblib.load(MODEL_PATH)
    except Exception as exc:
        raise HTTPException(status_code=500, detail="ML model is not available") from exc
    return _MODEL


def build_model_input(features: dict) -> pd.DataFrame:
    return pd.DataFrame(
        [[
            features["mar_avg_temp"],
            features["aug_sunshine"],
            features["oct_rainfall"],
            features["aug_humidity"],
        ]],
        columns=FEATURES,
    )


def serialize_prediction(prediction: MLPrediction) -> dict:
    snapshot = prediction.open_api_snapshot_json or {}
    unit_yield_kg_10a = snapshot.get("unit_yield_kg_10a")
    return {
        "prediction_id": prediction.prediction_id,
        "farm_id": prediction.farm_id,
        "product_id": prediction.product_id,
        "unit_yield_kg_10a": round(float(unit_yield_kg_10a), 2) if unit_yield_kg_10a is not None else None,
        "predicted_harvest_start": prediction.predicted_harvest_start,
        "predicted_harvest_end": prediction.predicted_harvest_end,
        "estimated_yield_kg": round(float(prediction.estimated_yield_kg), 2),
        "suggested_reservable_min_kg": round(float(prediction.suggested_reservable_min_kg), 2),
        "suggested_reservable_max_kg": round(float(prediction.suggested_reservable_max_kg), 2),
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
        model = get_model()
        input_df = build_model_input(features)
        try:
            unit_yield_kg_10a = float(model.predict(input_df)[0])
        except Exception as exc:
            raise HTTPException(status_code=500, detail="ML prediction failed") from exc

        variety_weight = 1.1 if features["variety"] == APPLE_VARIETY_FUJI else 1.0
        estimated_yield_kg = round((unit_yield_kg_10a / 1500.0) * features["past_yield_kg"] * variety_weight, 2)
        suggested_reservable_min_kg = round(estimated_yield_kg * 0.4, 2)
        suggested_reservable_max_kg = round(estimated_yield_kg * 0.75, 2)
        recommended_price = int(features["market_price"] * variety_weight)
        predicted_harvest_start = date.today() + timedelta(days=30)
        predicted_harvest_end = predicted_harvest_start + timedelta(days=14)

        prediction = MLPrediction(
            farm_id=farm.farm_id,
            product_id=product.product_id,
            created_by_owner_id=owner_id,
            input_feature_json=features,
            open_api_snapshot_json={
                "source": "manual_input",
                "model": MODEL_VERSION,
                "unit_yield_kg_10a": round(unit_yield_kg_10a, 2),
            },
            predicted_harvest_start=predicted_harvest_start,
            predicted_harvest_end=predicted_harvest_end,
            estimated_yield_kg=estimated_yield_kg,
            suggested_reservable_min_kg=suggested_reservable_min_kg,
            suggested_reservable_max_kg=suggested_reservable_max_kg,
            recommended_price=recommended_price,
            confidence=0.78,
            safety_factor=0.75,
            warning_message=NORMAL_WARNING_MESSAGE,
            model_version=MODEL_VERSION,
        )
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
