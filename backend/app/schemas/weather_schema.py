from pydantic import BaseModel, ConfigDict, Field


class WeatherFeatureQuery(BaseModel):
    stn_id: str | None = Field(default=None, min_length=1, json_schema_extra={"example": "136"})
    target_year: int = Field(ge=1900, le=2100, json_schema_extra={"example": 2026})

    model_config = ConfigDict(extra="forbid")


class WeatherFeatureResponse(BaseModel):
    target_year: int
    stn_id: str
    mar_avg_temp: float
    aug_sunshine: float
    oct_rainfall: float
    aug_humidity: float
    source: str
    fallback_used: bool
    fallback_year: int | None = None
    fallback_reason: str | None = None
    feature_source_years: dict[str, int]


class WeatherFeatureBundle(BaseModel):
    mar_avg_temp: float
    aug_sunshine: float
    oct_rainfall: float
    aug_humidity: float
    source: str
    fallback_used: bool
    fallback_year: int | None = None
    fallback_reason: str | None = None
    feature_source_years: dict[str, int]
