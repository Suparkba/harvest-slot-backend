# Harvest Slot Backend

FastAPI + SQLAlchemy + MySQL based backend for the Harvest Slot project.

## Run

```powershell
pip install -r requirements.txt
$env:PYTHONPATH = (Get-Location).Path
uvicorn backend.app.main:app --reload
```

- Swagger: `http://127.0.0.1:8000/docs`
- API base path: `/api/v1`

## Core Notes

- Keep the existing app entrypoint: `backend.app.main:app`
- Common response format: `{ "data": ..., "message": "success", "error": null }`
- Owner ML prediction endpoint: `POST /api/v1/owner/ml/predictions`

## ML Prediction API

Request example:

```json
{
  "farm_id": 1,
  "product_id": 1,
  "features": {
    "past_yield_kg": 3000,
    "market_price": 5000,
    "variety": "부사",
    "mar_avg_temp": 8.5,
    "aug_sunshine": 210.0,
    "oct_rainfall": 65.0,
    "aug_humidity": 72.0
  }
}
```

Response example:

```json
{
  "data": {
    "prediction_id": 1,
    "farm_id": 1,
    "product_id": 1,
    "unit_yield_kg_10a": 1509.53,
    "predicted_harvest_start": "YYYY-MM-DD",
    "predicted_harvest_end": "YYYY-MM-DD",
    "estimated_yield_kg": 3321.50,
    "suggested_reservable_min_kg": 1328.60,
    "suggested_reservable_max_kg": 2491.13,
    "recommended_price": 5500,
    "confidence": 0.78,
    "safety_factor": 0.75,
    "warning_message": "정상",
    "model_version": "rf-apple-harvest-v1"
  },
  "message": "success",
  "error": null
}
```

실제 ML 예측을 실행하려면 `model.joblib` 파일을 `backend/app/ml_models/model.joblib` 경로에 직접 배치해야 합니다.

## API Docs

- `docs/api/ml_prediction_api.md`
- `docs/api/frontend_integration_guide.md`
- `docs/api/examples/ml_prediction_request.json`
- `docs/api/examples/ml_prediction_response.json`
