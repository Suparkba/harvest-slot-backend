from pydantic import BaseModel, ConfigDict, Field


class PaymentMockApproveRequest(BaseModel):
    order_id: int = Field(json_schema_extra={"example": 1})
    idempotency_key: str = Field(json_schema_extra={"example": "payment-order-1-try-1"})

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "order_id": 1,
                "idempotency_key": "payment-order-1-try-1",
            }
        }
    )
