from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class MLPredictionFeatures(BaseModel):
    past_yield_kg: float = Field(gt=0, json_schema_extra={"example": 3000})
    market_price: float = Field(gt=0, json_schema_extra={"example": 5000})
    variety: str = Field(min_length=1, json_schema_extra={"example": "\ubd80\uc0ac"})
    mar_avg_temp: float = Field(ge=-5, le=25, json_schema_extra={"example": 8.5})
    aug_sunshine: float = Field(ge=50, le=400, json_schema_extra={"example": 210.0})
    oct_rainfall: float = Field(ge=0, le=600, json_schema_extra={"example": 65.0})
    aug_humidity: float = Field(ge=30, le=100, json_schema_extra={"example": 72.0})

    model_config = ConfigDict(extra="forbid")


class MLPredictionCreateRequest(BaseModel):
    farm_id: int
    product_id: int
    features: MLPredictionFeatures

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "farm_id": 1,
                "product_id": 1,
                "features": {
                    "past_yield_kg": 3000,
                    "market_price": 5000,
                    "variety": "\ubd80\uc0ac",
                    "mar_avg_temp": 8.5,
                    "aug_sunshine": 210.0,
                    "oct_rainfall": 65.0,
                    "aug_humidity": 72.0,
                },
            }
        }
    )


class MLPredictionResponse(BaseModel):
    prediction_id: int
    farm_id: int
    product_id: int
    unit_yield_kg_10a: float | None = None
    predicted_harvest_start: date
    predicted_harvest_end: date
    estimated_yield_kg: float
    suggested_reservable_min_kg: float
    suggested_reservable_max_kg: float
    recommended_price: int
    confidence: float
    safety_factor: float
    warning_message: str
    model_version: str
