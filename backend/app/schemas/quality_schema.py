from pydantic import BaseModel, ConfigDict, Field


class QualityInspectionCreateRequest(BaseModel):
    procurement_item_id: int = Field(json_schema_extra={"example": 1})
    image_url: str = Field(json_schema_extra={"example": "/mock/quality/apple_sample_001.jpg"})
    owner_confirmed_grade: str | None = Field(default=None, json_schema_extra={"example": "A"})
    owner_decision: str | None = Field(default=None, json_schema_extra={"example": "PASS"})

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "procurement_item_id": 1,
                "image_url": "/mock/quality/apple_sample_001.jpg",
                "owner_confirmed_grade": "A",
                "owner_decision": "PASS",
            }
        }
    )


class QualityInspectionAnalyzeRequest(BaseModel):
    procurement_item_id: int = Field(json_schema_extra={"example": 1})
    image_url: str | None = Field(default=None, json_schema_extra={"example": "https://cdn.example.com/quality/apple_001.jpg"})
    persist_image: bool = Field(default=False, json_schema_extra={"example": False})

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "procurement_item_id": 1,
                "image_url": "https://cdn.example.com/quality/apple_001.jpg",
                "persist_image": False,
            }
        }
    )
