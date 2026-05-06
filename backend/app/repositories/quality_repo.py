from sqlalchemy import desc, select

from backend.app.models.quality_inspection import QualityInspection
from backend.app.repositories.base_repo import BaseRepository


class QualityRepository(BaseRepository):
    def list_by_owner(self, owner_id: int) -> list[QualityInspection]:
        stmt = (
            select(QualityInspection)
            .where(QualityInspection.owner_id == owner_id)
            .order_by(desc(QualityInspection.created_at))
        )
        return list(self.session.scalars(stmt).all())
