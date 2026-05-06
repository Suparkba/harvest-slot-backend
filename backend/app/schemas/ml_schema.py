from datetime import date

from pydantic import BaseModel


class MLPredictionCreateRequest(BaseModel):
    farm_id: int
    product_id: int
    features: dict


class MLPredictionResponse(BaseModel):
    prediction_id: int
    predicted_harvest_start: date
    predicted_harvest_end: date
    estimated_yield_kg: float
    suggested_reservable_min_kg: float
    suggested_reservable_max_kg: float
    recommended_price: int
    confidence: float
    safety_factor: float
    warning_message: str
