from pydantic import BaseModel


class ProcurementDecisionItemRequest(BaseModel):
    procurement_item_id: int
    approved_package_count: int
    approved_kg: float
    owner_memo: str | None = None


class ProcurementDecisionRequest(BaseModel):
    decision: str
    items: list[ProcurementDecisionItemRequest]
    rejected_reason: str | None = None
