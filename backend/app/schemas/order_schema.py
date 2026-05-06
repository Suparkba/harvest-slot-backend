from pydantic import BaseModel


class OrderFromReservationRequest(BaseModel):
    reservation_id: int
    receiver_name: str
    receiver_phone: str
    shipping_address: str
    delivery_memo: str | None = None
