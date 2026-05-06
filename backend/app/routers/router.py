from fastapi import APIRouter

from backend.app.routers.auth_router import router as auth_router
from backend.app.routers.harvest_slot_router import router as harvest_slot_router
from backend.app.routers.health_router import router as health_router
from backend.app.routers.ml_router import router as ml_router
from backend.app.routers.order_router import router as order_router
from backend.app.routers.owner_router import router as owner_router
from backend.app.routers.payment_router import router as payment_router
from backend.app.routers.procurement_router import router as procurement_router
from backend.app.routers.product_router import router as product_router
from backend.app.routers.quality_router import router as quality_router
from backend.app.routers.reservation_router import router as reservation_router
from backend.app.routers.return_router import router as return_router
from backend.app.routers.shipment_router import router as shipment_router


api_router = APIRouter()
api_router.include_router(health_router, tags=["health"])
api_router.include_router(auth_router, tags=["auth"])
api_router.include_router(product_router, tags=["products"])
api_router.include_router(owner_router, tags=["owner"])
api_router.include_router(ml_router, tags=["ml"])
api_router.include_router(harvest_slot_router, tags=["harvest-slots"])
api_router.include_router(reservation_router, tags=["reservations"])
api_router.include_router(order_router, tags=["orders"])
api_router.include_router(payment_router, tags=["payments"])
api_router.include_router(procurement_router, tags=["procurements"])
api_router.include_router(quality_router, tags=["quality"])
api_router.include_router(shipment_router, tags=["shipments"])
api_router.include_router(return_router, tags=["returns"])
