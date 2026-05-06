from pydantic import BaseModel


class ReturnCreateRequest(BaseModel):
    order_id: int
    reason_code: str
    reason_detail: str | None = None
    evidence_image_url: str | None = None
    requested_amount: int


class ReturnDecisionRequest(BaseModel):
    decision: str
    approved_amount: int
    decision_reason: str | None = None
