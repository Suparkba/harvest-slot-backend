from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.security import AuthenticatedUser, require_owner
from backend.app.schemas.common_schema import success_response
from backend.app.schemas.ml_schema import MLAutoWeatherPredictionRequest, MLPredictionCreateRequest
from backend.app.services.ml_service import MLService


router = APIRouter()


@router.post("/owner/ml/predictions")
def create_prediction(
    payload: MLPredictionCreateRequest,
    current_user: AuthenticatedUser = Depends(require_owner),
    db: Session = Depends(get_db),
) -> dict:
    return success_response(MLService(db).create_prediction(current_user.owner_id, payload.model_dump()))


@router.post("/owner/ml/predictions/auto-weather")
def create_prediction_auto_weather(
    payload: MLAutoWeatherPredictionRequest,
    current_user: AuthenticatedUser = Depends(require_owner),
    db: Session = Depends(get_db),
) -> dict:
    return success_response(MLService(db).create_prediction_with_auto_weather(current_user.owner_id, payload.model_dump()))


@router.get("/owner/ml/predictions")
def list_predictions(
    current_user: AuthenticatedUser = Depends(require_owner),
    db: Session = Depends(get_db),
) -> dict:
    return success_response(MLService(db).list_predictions(current_user.owner_id))


@router.get("/owner/ml/predictions/{prediction_id}")
def get_prediction(
    prediction_id: int,
    current_user: AuthenticatedUser = Depends(require_owner),
    db: Session = Depends(get_db),
) -> dict:
    return success_response(MLService(db).get_prediction(current_user.owner_id, prediction_id))
