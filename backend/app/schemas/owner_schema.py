from pydantic import BaseModel


class OwnerDashboardResponse(BaseModel):
    open_slots: int
    new_procurements: int
    quality_waiting: int
    ready_to_ship: int
    return_requests: int


class OwnerProfileUpdateRequest(BaseModel):
    owner_name: str
    owner_phone: str
    business_number: str | None = None
