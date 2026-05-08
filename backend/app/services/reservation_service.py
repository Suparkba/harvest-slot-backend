from datetime import datetime, timedelta
import logging

from fastapi import HTTPException
from sqlalchemy.orm import Session

from backend.app.core.status import HarvestSlotStatus, ReservationStatus
from backend.app.core.transaction import transaction_scope
from backend.app.models.harvest_slot import HarvestSlot
from backend.app.models.reservation import Reservation, ReservationItem
from backend.app.repositories.harvest_slot_repo import HarvestSlotRepository
from backend.app.repositories.reservation_repo import ReservationRepository

logger = logging.getLogger(__name__)

VISIBLE_RESERVATION_STATUSES = (
    ReservationStatus.RESERVED,
    ReservationStatus.ORDERED,
    ReservationStatus.EXPIRED,
    ReservationStatus.CANCELED,
)


def calculate_available_kg(slot: HarvestSlot) -> float:
    return float(slot.confirmed_reservable_kg) - float(slot.reserved_kg) - float(slot.sold_kg)


def calculate_reserved_kg(package_count: int, package_unit_kg: float) -> float:
    return round(package_count * package_unit_kg, 2)


def ensure_quantity_available(requested_kg: float, available_kg: float) -> None:
    if requested_kg > available_kg:
        raise HTTPException(status_code=400, detail="requested quantity exceeds available_kg")


def serialize_reservation(reservation: Reservation) -> dict:
    return {
        "reservation_id": reservation.reservation_id,
        "reservation_no": reservation.reservation_no,
        "reservation_status": reservation.reservation_status,
        "customer_id": reservation.customer_id,
        "customer_name": reservation.customer.customer_name if reservation.customer else None,
        "reserved_until": reservation.reserved_until,
        "total_reserved_kg": float(reservation.total_reserved_kg),
        "total_amount": reservation.total_amount,
        "order_id": reservation.order.order_id if reservation.order else None,
        "order_no": reservation.order.order_no if reservation.order else None,
        "order_status": reservation.order.order_status if reservation.order else None,
        "items": [
            {
                "reservation_item_id": item.reservation_item_id,
                "slot_id": item.slot_id,
                "product_id": item.slot.product_id if item.slot else None,
                "product_name": item.slot.product.product_name if item.slot and item.slot.product else None,
                "farm_id": item.slot.farm_id if item.slot else None,
                "farm_name": item.slot.farm.farm_name if item.slot and item.slot.farm else None,
                "image_url": item.slot.product.image_url if item.slot and item.slot.product else None,
                "package_count": item.package_count,
                "reserved_kg": float(item.reserved_kg),
                "unit_price_snapshot": item.unit_price_snapshot,
                "subtotal_amount": item.subtotal_amount,
            }
            for item in reservation.reservation_items
        ],
    }


class ReservationService:
    def __init__(self, session: Session):
        self.session = session
        self.slot_repo = HarvestSlotRepository(session)
        self.reservation_repo = ReservationRepository(session)

    def preview(self, items: list[dict]) -> dict:
        slot_ids = [item["slot_id"] for item in items]
        slots = {slot.slot_id: slot for slot in self.slot_repo.lock_slots(slot_ids)}
        preview_items: list[dict] = []
        total_reserved_kg = 0.0
        total_amount = 0

        for item in items:
            slot = slots.get(item["slot_id"])
            if not slot or slot.slot_status != HarvestSlotStatus.OPEN:
                raise HTTPException(status_code=404, detail="slot not available")
            package_unit_kg = float(slot.product.package_unit_kg)
            reserved_kg = calculate_reserved_kg(item["package_count"], package_unit_kg)
            available_kg = calculate_available_kg(slot)
            ensure_quantity_available(reserved_kg, available_kg)
            subtotal_amount = item["package_count"] * slot.confirmed_price
            preview_items.append(
                {
                    "slot_id": slot.slot_id,
                    "package_count": item["package_count"],
                    "reserved_kg": reserved_kg,
                    "unit_price_snapshot": slot.confirmed_price,
                    "subtotal_amount": subtotal_amount,
                    "available_kg": available_kg,
                }
            )
            total_reserved_kg += reserved_kg
            total_amount += subtotal_amount

        return {
            "items": preview_items,
            "total_reserved_kg": round(total_reserved_kg, 2),
            "total_amount": total_amount,
        }

    def create_reservation(self, customer_id: int, items: list[dict]) -> dict:
        with transaction_scope(self.session):
            slot_ids = [item["slot_id"] for item in items]
            slots = {slot.slot_id: slot for slot in self.slot_repo.lock_slots(slot_ids)}
            created_items: list[ReservationItem] = []
            total_reserved_kg = 0.0
            total_amount = 0

            for item in items:
                slot = slots.get(item["slot_id"])
                if not slot or slot.slot_status != HarvestSlotStatus.OPEN:
                    raise HTTPException(status_code=404, detail="slot not available")

                package_unit_kg = float(slot.product.package_unit_kg)
                reserved_kg = calculate_reserved_kg(item["package_count"], package_unit_kg)
                ensure_quantity_available(reserved_kg, calculate_available_kg(slot))
                subtotal_amount = item["package_count"] * slot.confirmed_price

                created_items.append(
                    ReservationItem(
                        slot_id=slot.slot_id,
                        package_count=item["package_count"],
                        reserved_kg=reserved_kg,
                        unit_price_snapshot=slot.confirmed_price,
                        subtotal_amount=subtotal_amount,
                    )
                )
                total_reserved_kg += reserved_kg
                total_amount += subtotal_amount

            reservation = Reservation(
                customer_id=customer_id,
                reservation_no=f"RSV-{int(datetime.utcnow().timestamp())}",
                reservation_status=ReservationStatus.RESERVED,
                reserved_until=datetime.utcnow() + timedelta(minutes=30),
                total_reserved_kg=round(total_reserved_kg, 2),
                total_amount=total_amount,
            )
            self.session.add(reservation)
            self.session.flush()

            for created_item in created_items:
                created_item.reservation_id = reservation.reservation_id
                self.session.add(created_item)

                slot = slots[created_item.slot_id]
                slot.reserved_kg = round(float(slot.reserved_kg) + float(created_item.reserved_kg), 2)

            self.session.flush()
            self.session.refresh(reservation)
            return serialize_reservation(reservation)

    def list_my_reservations(self, customer_id: int) -> list[dict]:
        rows = self.reservation_repo.list_for_customer(customer_id, VISIBLE_RESERVATION_STATUSES)
        logger.info(
            "list_my_reservations customer_id=%s reservation_ids=%s",
            customer_id,
            [row.reservation_id for row in rows],
        )
        return [serialize_reservation(row) for row in rows]

    def list_owner_reservations(self, owner_id: int) -> list[dict]:
        rows = self.session.query(Reservation).distinct().order_by(Reservation.created_at.desc()).all()
        filtered = [row for row in rows if any(item.slot.farm.owner_id == owner_id for item in row.reservation_items)]
        return [serialize_reservation(row) for row in filtered]
