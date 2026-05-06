from pydantic import BaseModel


class PaymentMockApproveRequest(BaseModel):
    order_id: int
    idempotency_key: str
