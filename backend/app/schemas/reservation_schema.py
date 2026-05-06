from datetime import datetime

from pydantic import BaseModel


class ReservationItemRequest(BaseModel):
    slot_id: int
    package_count: int


class ReservationPreviewRequest(BaseModel):
    items: list[ReservationItemRequest]


class ReservationCreateRequest(ReservationPreviewRequest):
    pass


class ReservationItemResponse(BaseModel):
    slot_id: int
    package_count: int
    reserved_kg: float
    unit_price_snapshot: int
    subtotal_amount: int


class ReservationResponse(BaseModel):
    reservation_id: int
    reservation_no: str
    reservation_status: str
    reserved_until: datetime
    total_reserved_kg: float
    total_amount: int
    items: list[ReservationItemResponse]
