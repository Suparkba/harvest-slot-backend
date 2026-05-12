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
from backend.app.services.weather_feature_service import WeatherFeatureService

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


def get_ml_model() -> Any:
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


def build_model_input(features: dict[str, Any]) -> pd.DataFrame:
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
        self.weather_feature_service = WeatherFeatureService()

    def create_prediction(self, owner_id: int, payload: dict) -> dict:
        features, weather_bundle = self.weather_feature_service.merge_weather_features(payload["features"])
        prediction = self._create_prediction_record(
            owner_id=owner_id,
            farm_id=payload["farm_id"],
            product_id=payload["product_id"],
            features=features,
            weather_bundle=weather_bundle,
        )
        return serialize_prediction(prediction)

    def create_prediction_with_auto_weather(self, owner_id: int, payload: dict) -> dict:
        weather_bundle = self.weather_feature_service.get_weather_features(
            target_year=payload["target_year"],
            stn_id=payload.get("stn_id"),
        )
        features = {
            "past_yield_kg": payload["past_yield_kg"],
            "market_price": payload["market_price"],
            "variety": payload["variety"],
            "target_year": payload["target_year"],
            "stn_id": weather_bundle["stn_id"],
            "mar_avg_temp": weather_bundle["mar_avg_temp"],
            "aug_sunshine": weather_bundle["aug_sunshine"],
            "oct_rainfall": weather_bundle["oct_rainfall"],
            "aug_humidity": weather_bundle["aug_humidity"],
        }
        prediction = self._create_prediction_record(
            owner_id=owner_id,
            farm_id=payload["farm_id"],
            product_id=payload["product_id"],
            features=features,
            weather_bundle=weather_bundle,
        )
        serialized = serialize_prediction(prediction)
        serialized["weather_features"] = {
            "mar_avg_temp": weather_bundle["mar_avg_temp"],
            "aug_sunshine": weather_bundle["aug_sunshine"],
            "oct_rainfall": weather_bundle["oct_rainfall"],
            "aug_humidity": weather_bundle["aug_humidity"],
        }
        serialized["weather_source"] = {
            "source": weather_bundle["source"],
            "fallback_used": weather_bundle["fallback_used"],
            "fallback_year": weather_bundle["fallback_year"],
            "fallback_reason": weather_bundle["fallback_reason"],
            "feature_source_years": weather_bundle["feature_source_years"],
        }
        return serialized

    def _validate_prediction_target(self, owner_id: int, farm_id: int, product_id: int) -> tuple[Any, Any]:
        farm = self.farm_repo.get(farm_id)
        product = self.product_repo.get(product_id)
        if not farm or farm.owner_id != owner_id:
            raise HTTPException(status_code=404, detail="farm not found")
        if not product or product.farm_id != farm.farm_id:
            raise HTTPException(status_code=404, detail="product not found")
        return farm, product

    def _create_prediction_record(
        self,
        *,
        owner_id: int,
        farm_id: int,
        product_id: int,
        features: dict[str, Any],
        weather_bundle: dict[str, Any] | None,
    ) -> MLPrediction:
        farm, product = self._validate_prediction_target(owner_id, farm_id, product_id)
        model = get_ml_model()
        input_df = build_model_input(features)
        try:
            unit_yield_kg_10a = round(float(model.predict(input_df)[0]), 2)
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
                "source": weather_bundle["source"] if weather_bundle else "manual_input",
                "model": MODEL_VERSION,
                "unit_yield_kg_10a": unit_yield_kg_10a,
                "weather_feature_snapshot": weather_bundle,
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
        return prediction

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
