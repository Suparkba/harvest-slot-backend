from pydantic import BaseModel, Field


class ReturnCreateRequest(BaseModel):
    order_id: int
    reason_code: str
    reason_detail: str | None = None
    evidence_image_url: str | None = None
    requested_amount: int


class ReturnDecisionRequest(BaseModel):
    decision: str
    approved_amount: int = Field(ge=0)
    decision_reason: str | None = None
