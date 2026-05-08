from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ReservationItemRequest(BaseModel):
    slot_id: int = Field(json_schema_extra={"example": 1})
    package_count: int = Field(json_schema_extra={"example": 2})


class ReservationPreviewRequest(BaseModel):
    items: list[ReservationItemRequest]

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [
                    {
                        "slot_id": 1,
                        "package_count": 2,
                    }
                ]
            }
        }
    )


class ReservationCreateRequest(ReservationPreviewRequest):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [
                    {
                        "slot_id": 1,
                        "package_count": 2,
                    }
                ]
            }
        }
    )


class ReservationItemResponse(BaseModel):
    slot_id: int
    package_count: int
    reserved_kg: float
    unit_price_snapshot: int
    subtotal_amount: int


class ReservationResponse(BaseModel):
    reservation_id: int
    reservation_no: str
    reservation_status: str
    reserved_until: datetime
    total_reserved_kg: float
    total_amount: int
    items: list[ReservationItemResponse]
