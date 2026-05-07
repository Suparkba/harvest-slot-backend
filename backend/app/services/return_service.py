from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.core.status import OrderItemStatus, OrderStatus, PaymentStatus, RefundStatus, ReturnStatus
from backend.app.core.transaction import transaction_scope
from backend.app.models.return_refund import Refund, ReturnRequest
from backend.app.repositories.order_repo import OrderRepository
from backend.app.repositories.return_repo import ReturnRepository


def serialize_return_request(return_request: ReturnRequest) -> dict:
    return {
        "return_request_id": return_request.return_request_id,
        "order_id": return_request.order_id,
        "return_no": return_request.return_no,
        "return_status": return_request.return_status,
        "reason_code": return_request.reason_code,
        "reason_detail": return_request.reason_detail,
        "evidence_image_url": return_request.evidence_image_url,
        "requested_amount": return_request.requested_amount,
        "approved_amount": return_request.approved_amount,
        "decision_reason": return_request.decision_reason,
        "requested_at": return_request.requested_at,
        "decided_at": return_request.decided_at,
        "refund": (
            {
                "refund_id": return_request.refund.refund_id,
                "refund_status": return_request.refund.refund_status,
                "refunded_amount": return_request.refund.refunded_amount,
            }
            if return_request.refund
            else None
        ),
    }


class ReturnService:
    def __init__(self, session: Session):
        self.session = session
        self.order_repo = OrderRepository(session)
        self.return_repo = ReturnRepository(session)

    def create_return_request(self, customer_id: int, payload: dict) -> dict:
        order = self.order_repo.get(payload["order_id"])
        if not order or order.reservation.customer_id != customer_id:
            raise HTTPException(status_code=404, detail="order not found")
        if order.order_status != OrderStatus.DELIVERED:
            raise HTTPException(status_code=400, detail="only delivered orders can be returned")
        if order.return_request:
            raise HTTPException(status_code=400, detail="return request already exists")

        return_request = ReturnRequest(
            order_id=order.order_id,
            return_no=f"RET-{int(datetime.utcnow().timestamp())}",
            return_status=ReturnStatus.REQUESTED,
            reason_code=payload["reason_code"],
            reason_detail=payload.get("reason_detail"),
            evidence_image_url=payload.get("evidence_image_url"),
            requested_amount=payload["requested_amount"],
            approved_amount=0,
            requested_at=datetime.utcnow(),
        )
        self.session.add(return_request)
        order.order_status = OrderStatus.RETURN_REQUESTED
        self.session.commit()
        self.session.refresh(return_request)
        return serialize_return_request(return_request)

    def list_owner_returns(self, owner_id: int) -> list[dict]:
        rows = self.session.query(ReturnRequest).all()
        filtered = [row for row in rows if row.order.procurement and row.order.procurement.owner_id == owner_id]
        return [serialize_return_request(row) for row in filtered]

    @staticmethod
    def _validate_decision(decision: str) -> None:
        if decision not in {ReturnStatus.APPROVED, ReturnStatus.REJECTED}:
            raise HTTPException(status_code=400, detail="invalid return decision")

    @staticmethod
    def _ensure_return_not_decided(return_request: ReturnRequest) -> None:
        if return_request.return_status in {ReturnStatus.APPROVED, ReturnStatus.REJECTED, ReturnStatus.REFUNDED}:
            raise HTTPException(status_code=400, detail="return request already decided")

    @staticmethod
    def _resolve_approved_payment(return_request: ReturnRequest):
        approved_payment = next(
            (payment for payment in return_request.order.payments if payment.payment_status == PaymentStatus.APPROVED),
            None,
        )
        if not approved_payment:
            raise HTTPException(status_code=400, detail="approved payment not found")
        return approved_payment

    @staticmethod
    def _validate_approved_amount(return_request: ReturnRequest, approved_payment, approved_amount: int) -> None:
        if approved_amount < 0:
            raise HTTPException(status_code=400, detail="approved amount must be zero or greater")
        if approved_amount > return_request.requested_amount:
            raise HTTPException(status_code=400, detail="approved amount exceeds requested amount")
        if approved_amount > approved_payment.approved_amount:
            raise HTTPException(status_code=400, detail="approved amount exceeds payment amount")

    def decide_return(self, owner_id: int, return_request_id: int, payload: dict) -> dict:
        try:
            with transaction_scope(self.session):
                return_request = self.return_repo.lock_return_request(return_request_id)
                if (
                    not return_request
                    or not return_request.order.procurement
                    or return_request.order.procurement.owner_id != owner_id
                ):
                    raise HTTPException(status_code=404, detail="return request not found")

                decision = payload["decision"]
                approved_amount = payload["approved_amount"]
                self._validate_decision(decision)
                self._ensure_return_not_decided(return_request)

                if return_request.refund:
                    raise HTTPException(status_code=400, detail="refund already exists")

                return_request.decision_reason = payload.get("decision_reason")
                return_request.decided_at = datetime.utcnow()

                if decision == ReturnStatus.APPROVED:
                    approved_payment = self._resolve_approved_payment(return_request)
                    self._validate_approved_amount(return_request, approved_payment, approved_amount)

                    return_request.return_status = ReturnStatus.REFUNDED
                    return_request.approved_amount = approved_amount
                    self.session.add(
                        Refund(
                            return_request_id=return_request.return_request_id,
                            payment_id=approved_payment.payment_id,
                            refund_status=RefundStatus.COMPLETED,
                            requested_amount=return_request.requested_amount,
                            refunded_amount=approved_amount,
                            requested_at=datetime.utcnow(),
                            completed_at=datetime.utcnow(),
                        )
                    )
                    approved_payment.payment_status = PaymentStatus.REFUNDED
                    return_request.order.order_status = OrderStatus.REFUNDED
                    for order_item in return_request.order.order_items:
                        order_item.order_item_status = OrderItemStatus.REFUNDED
                else:
                    return_request.return_status = ReturnStatus.REJECTED
                    return_request.approved_amount = 0

                self.session.flush()
                self.session.refresh(return_request)
        except IntegrityError as exc:
            self.session.rollback()
            raise HTTPException(status_code=400, detail="refund already exists") from exc

        return serialize_return_request(return_request)

    def list_my_returns(self, customer_id: int) -> list[dict]:
        rows = self.session.query(ReturnRequest).all()
        filtered = [row for row in rows if row.order.reservation.customer_id == customer_id]
        return [serialize_return_request(row) for row in filtered]
