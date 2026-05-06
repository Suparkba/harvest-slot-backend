from pydantic import BaseModel


class QualityInspectionCreateRequest(BaseModel):
    procurement_item_id: int
    image_url: str
    owner_confirmed_grade: str | None = None
    owner_decision: str | None = None
