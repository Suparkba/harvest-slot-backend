from pydantic import BaseModel, ConfigDict, Field


class ReturnCreateRequest(BaseModel):
    order_id: int = Field(json_schema_extra={"example": 1})
    reason_code: str = Field(json_schema_extra={"example": "QUALITY_ISSUE"})
    reason_detail: str | None = Field(
        default=None,
        json_schema_extra={"example": "상품 품질 문제로 반품 요청합니다."},
    )
    evidence_image_url: str | None = Field(
        default=None,
        json_schema_extra={"example": "/mock/returns/apple_damage_001.jpg"},
    )
    requested_amount: int = Field(json_schema_extra={"example": 78000})

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "order_id": 1,
                "reason_code": "QUALITY_ISSUE",
                "reason_detail": "상품 품질 문제로 반품 요청합니다.",
                "evidence_image_url": "/mock/returns/apple_damage_001.jpg",
                "requested_amount": 78000,
            }
        }
    )


class ReturnDecisionRequest(BaseModel):
    decision: str = Field(json_schema_extra={"example": "APPROVED"})
    approved_amount: int = Field(ge=0, json_schema_extra={"example": 39000})
    decision_reason: str | None = Field(default=None, json_schema_extra={"example": "반품 승인 및 환불 완료"})

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "decision": "APPROVED",
                "approved_amount": 39000,
                "decision_reason": "반품 승인 및 환불 완료",
            }
        }
    )
