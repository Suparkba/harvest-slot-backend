from pydantic import BaseModel, ConfigDict, Field


class ShipmentCreateRequest(BaseModel):
    order_id: int = Field(json_schema_extra={"example": 1})
    carrier_name: str = Field(json_schema_extra={"example": "CJ대한통운"})
    tracking_no: str = Field(json_schema_extra={"example": "1234567890"})
    shipped_package_count: int = Field(json_schema_extra={"example": 2})
    shipped_kg: float = Field(json_schema_extra={"example": 10})

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "order_id": 1,
                "carrier_name": "CJ대한통운",
                "tracking_no": "1234567890",
                "shipped_package_count": 2,
                "shipped_kg": 10,
            }
        }
    )


class ShipmentStatusUpdateRequest(BaseModel):
    shipment_status: str = Field(json_schema_extra={"example": "DELIVERED"})

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "shipment_status": "DELIVERED",
            }
        }
    )
