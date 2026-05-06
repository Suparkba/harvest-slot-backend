from pydantic import BaseModel


class ShipmentCreateRequest(BaseModel):
    order_id: int
    carrier_name: str
    tracking_no: str
    shipped_package_count: int
    shipped_kg: float


class ShipmentStatusUpdateRequest(BaseModel):
    shipment_status: str
