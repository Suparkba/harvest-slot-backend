from pydantic import BaseModel, ConfigDict, Field


class ProcurementDecisionItemRequest(BaseModel):
    procurement_item_id: int = Field(json_schema_extra={"example": 1})
    approved_package_count: int = Field(json_schema_extra={"example": 2})
    approved_kg: float = Field(json_schema_extra={"example": 10.0})
    owner_memo: str | None = Field(default=None, json_schema_extra={"example": "정상 수량 확인"})


class ProcurementDecisionRequest(BaseModel):
    decision: str = Field(json_schema_extra={"example": "APPROVED"})
    items: list[ProcurementDecisionItemRequest]
    rejected_reason: str | None = Field(default=None, json_schema_extra={"example": None})

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "decision": "APPROVED",
                "items": [
                    {
                        "procurement_item_id": 1,
                        "approved_package_count": 2,
                        "approved_kg": 10.0,
                        "owner_memo": "정상 수량 확인",
                    }
                ],
                "rejected_reason": None,
            }
        }
    )
