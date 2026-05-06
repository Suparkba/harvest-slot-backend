from pydantic import BaseModel, ConfigDict


class FarmUpdateRequest(BaseModel):
    farm_name: str
    farm_region: str
    farm_address: str
    farm_image_url: str | None = None
    farm_description: str | None = None
    delivery_policy: str | None = None
    return_policy: str | None = None


class ProductCreateRequest(BaseModel):
    farm_id: int
    product_name: str
    fruit_type: str
    variety: str
    package_unit_kg: float
    base_price: int
    image_url: str | None = None
    product_description: str | None = None
    product_status: str = "ACTIVE"


class ProductUpdateRequest(ProductCreateRequest):
    pass


class ProductStatusUpdateRequest(BaseModel):
    product_status: str


class ProductSummaryResponse(BaseModel):
    product_id: int
    farm_id: int
    product_name: str
    fruit_type: str
    variety: str
    package_unit_kg: float
    base_price: int
    product_status: str
    farm_name: str | None = None
    open_slot_count: int = 0
    image_url: str | None = None

    model_config = ConfigDict(from_attributes=True)
