from fastapi import HTTPException, UploadFile
from sqlalchemy import and_, case, func, select
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.status import HarvestSlotStatus, ProductStatus
from backend.app.models.farm import Farm
from backend.app.models.harvest_slot import HarvestSlot
from backend.app.models.product import Product
from backend.app.repositories.farm_repo import FarmRepository
from backend.app.repositories.product_repo import ProductRepository
from backend.app.services.image_storage_service import ImageStorageService


def serialize_farm(farm: Farm) -> dict:
    return {
        "farm_id": farm.farm_id,
        "owner_id": farm.owner_id,
        "farm_name": farm.farm_name,
        "farm_region": farm.farm_region,
        "farm_address": farm.farm_address,
        "farm_image_url": farm.farm_image_url,
        "farm_description": farm.farm_description,
        "delivery_policy": farm.delivery_policy,
        "return_policy": farm.return_policy,
    }


def serialize_product(product: Product, open_slot_count: int | None = None) -> dict:
    open_slots = [slot for slot in product.harvest_slots if slot.slot_status == HarvestSlotStatus.OPEN]
    min_open_price = min((slot.confirmed_price for slot in open_slots), default=product.base_price)
    return {
        "product_id": product.product_id,
        "farm_id": product.farm_id,
        "product_name": product.product_name,
        "fruit_type": product.fruit_type,
        "variety": product.variety,
        "package_unit_kg": float(product.package_unit_kg),
        "base_price": product.base_price,
        "product_status": product.product_status,
        "image_url": product.image_url,
        "product_description": product.product_description,
        "farm_name": product.farm.farm_name if product.farm else None,
        "farm_region": product.farm.farm_region if product.farm else None,
        "farm_image_url": product.farm.farm_image_url if product.farm else None,
        "open_slot_count": open_slot_count if open_slot_count is not None else 0,
        "min_open_slot_price": min_open_price,
    }


class ProductService:
    def __init__(self, session: Session):
        self.session = session
        self.product_repo = ProductRepository(session)
        self.farm_repo = FarmRepository(session)
        self.image_storage_service = ImageStorageService()

    def get_farm(self, farm_id: int) -> dict:
        farm = self.farm_repo.get(farm_id)
        if not farm:
            raise HTTPException(status_code=404, detail="farm not found")
        return serialize_farm(farm)

    def list_public_products(self, featured: bool | None = None, fruit_type: str | None = None) -> list[dict]:
        open_slot_count = func.count(HarvestSlot.slot_id)
        stmt = (
            select(Product, open_slot_count.label("open_slot_count"))
            .join(Farm, Product.farm_id == Farm.farm_id)
            .outerjoin(
                HarvestSlot,
                and_(
                    HarvestSlot.product_id == Product.product_id,
                    HarvestSlot.slot_status == HarvestSlotStatus.OPEN,
                ),
            )
            .where(Product.product_status == ProductStatus.ACTIVE)
            .group_by(Product.product_id, Farm.farm_id)
            .order_by(case((open_slot_count > 0, 0), else_=1), Product.created_at.desc())
        )
        if fruit_type:
            stmt = stmt.where(Product.fruit_type == fruit_type)
        if featured:
            stmt = stmt.having(open_slot_count > 0)
        rows = self.session.execute(stmt).all()
        return [serialize_product(product, int(count)) for product, count in rows]

    def get_product_detail(self, product_id: int) -> dict:
        product = self.product_repo.get(product_id)
        if not product:
            raise HTTPException(status_code=404, detail="product not found")
        data = serialize_product(product)
        data["farm"] = serialize_farm(product.farm)
        return data

    def get_owner_farms(self, owner_id: int) -> list[dict]:
        farms = self.farm_repo.list_by_owner(owner_id)
        return [serialize_farm(farm) for farm in farms]

    def update_farm(self, owner_id: int, farm_id: int, payload: dict) -> dict:
        farm = self.farm_repo.get(farm_id)
        if not farm or farm.owner_id != owner_id:
            raise HTTPException(status_code=404, detail="farm not found")
        for key, value in payload.items():
            setattr(farm, key, value)
        self.session.commit()
        self.session.refresh(farm)
        return serialize_farm(farm)

    def list_owner_products(self, owner_id: int) -> list[dict]:
        return [serialize_product(product) for product in self.product_repo.list_by_owner(owner_id)]

    def create_product(self, owner_id: int, payload: dict) -> dict:
        farm = self.farm_repo.get(payload["farm_id"])
        if not farm or farm.owner_id != owner_id:
            raise HTTPException(status_code=404, detail="farm not found")
        product = Product(**payload)
        self.session.add(product)
        self.session.commit()
        self.session.refresh(product)
        return serialize_product(product)

    def update_product(self, owner_id: int, product_id: int, payload: dict) -> dict:
        product = self.product_repo.get(product_id)
        if not product or product.farm.owner_id != owner_id:
            raise HTTPException(status_code=404, detail="product not found")
        for key, value in payload.items():
            setattr(product, key, value)
        self.session.commit()
        self.session.refresh(product)
        return serialize_product(product)

    def update_product_status(self, owner_id: int, product_id: int, product_status: str) -> dict:
        product = self.product_repo.get(product_id)
        if not product or product.farm.owner_id != owner_id:
            raise HTTPException(status_code=404, detail="product not found")
        product.product_status = product_status
        self.session.commit()
        self.session.refresh(product)
        return serialize_product(product)

    def upload_product_image(self, owner_id: int, product_id: int, upload: UploadFile) -> dict:
        product = self.product_repo.get(product_id)
        if not product or product.farm.owner_id != owner_id:
            raise HTTPException(status_code=404, detail="product not found")

        upload_result = self.image_storage_service.upload_image(
            upload,
            product_seq=product.product_id,
            subfolder=f"{settings.image_default_product_subfolder}/{product.farm_id}",
        )
        product.image_url = upload_result["file_url"]
        self.session.commit()
        self.session.refresh(product)

        data = serialize_product(product)
        data["file_name"] = upload_result["file_name"]
        data["subfolder"] = upload_result["subfolder"]
        return data
