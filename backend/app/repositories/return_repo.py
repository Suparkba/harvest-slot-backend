from sqlalchemy import select

from backend.app.models.return_refund import ReturnRequest
from backend.app.repositories.base_repo import BaseRepository


class ReturnRepository(BaseRepository):
    def get(self, return_request_id: int) -> ReturnRequest | None:
        return self.session.get(ReturnRequest, return_request_id)

    def lock_return_request(self, return_request_id: int) -> ReturnRequest | None:
        stmt = select(ReturnRequest).where(ReturnRequest.return_request_id == return_request_id).with_for_update()
        return self.session.scalar(stmt)
