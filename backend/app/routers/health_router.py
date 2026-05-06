from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from fastapi import APIRouter, Depends

from backend.app.core.database import get_db
from backend.app.schemas.common_schema import success_response


router = APIRouter()


@router.get("/health")
def health() -> dict:
    return success_response(
        {
            "status": "ok",
            "service": "harvest-slot-backend",
            "version": "1.0.0",
        }
    )


@router.get("/health/db")
def health_db(db: Session = Depends(get_db)) -> dict:
    try:
        db.execute(text("SELECT 1"))
        return success_response({"database": "connected"})
    except SQLAlchemyError as exc:
        return {"data": {"database": "disconnected"}, "message": "database connection failed", "error": str(exc)}
