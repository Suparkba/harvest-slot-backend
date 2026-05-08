from pydantic import BaseModel, ConfigDict, Field


class OrderFromReservationRequest(BaseModel):
    reservation_id: int = Field(json_schema_extra={"example": 1})
    receiver_name: str = Field(json_schema_extra={"example": "홍길동"})
    receiver_phone: str = Field(json_schema_extra={"example": "010-1111-2222"})
    shipping_address: str = Field(json_schema_extra={"example": "서울시 강남구 테헤란로 123"})
    delivery_memo: str | None = Field(default=None, json_schema_extra={"example": "문 앞에 놓아주세요"})

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "reservation_id": 1,
                "receiver_name": "홍길동",
                "receiver_phone": "010-1111-2222",
                "shipping_address": "서울시 강남구 테헤란로 123",
                "delivery_memo": "문 앞에 놓아주세요",
            }
        }
    )
