from datetime import date

from pydantic import BaseModel


class HarvestSlotCreateRequest(BaseModel):
    farm_id: int
    product_id: int
    prediction_id: int | None = None
    confirmed_harvest_start: date
    confirmed_harvest_end: date
    confirmed_reservable_kg: float
    confirmed_price: int
    customer_notice: str
    slot_status: str = "DRAFT"


class HarvestSlotUpdateRequest(HarvestSlotCreateRequest):
    pass


class HarvestSlotStatusUpdateRequest(BaseModel):
    slot_status: str
