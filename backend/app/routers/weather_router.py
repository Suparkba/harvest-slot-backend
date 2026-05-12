from fastapi import APIRouter, Query

from backend.app.schemas.common_schema import success_response
from backend.app.services.weather_feature_service import WeatherFeatureService


router = APIRouter(prefix="/weather")


@router.get("/features")
def get_weather_features(
    stn_id: str | None = Query(default=None, min_length=1),
    target_year: int = Query(..., ge=1900, le=2100),
) -> dict:
    return success_response(WeatherFeatureService().get_feature_bundle(target_year=target_year, stn_id=stn_id))
