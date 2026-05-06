from sqlalchemy import select

from backend.app.models.farm import Farm
from backend.app.repositories.base_repo import BaseRepository


class FarmRepository(BaseRepository):
    def get(self, farm_id: int) -> Farm | None:
        return self.session.get(Farm, farm_id)

    def list_by_owner(self, owner_id: int) -> list[Farm]:
        return list(self.session.scalars(select(Farm).where(Farm.owner_id == owner_id)).all())
