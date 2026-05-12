# Harvest Slot Backend

FastAPI backend for the Harvest Slot project.

## Run

```powershell
pip install -r requirements.txt
$env:PYTHONPATH = (Get-Location).Path
uvicorn backend.app.main:app --reload
```

## Core Runtime

- App entrypoint: `backend.app.main:app`
- API prefix: `/api/v1`
- Swagger: `http://127.0.0.1:8000/docs`
- ML model path: `backend/app/ml_models/model.joblib`

## KMA ASOS Environment Variables

`.env.example` should keep empty key values:

```env
KMA_ASOS_SERVICE_KEY=
KMA_ASOS_BASE_URL=http://apis.data.go.kr/1360000/AsosDalyInfoService/getWthrDataList
KMA_DEFAULT_STN_ID=136
```

Notes:

- Put the real `KMA_ASOS_SERVICE_KEY` only in `.env`
- Do not commit `.env`
- Do not place a real key in `.env.example`

## Main APIs

- `GET /api/v1/weather/features`
- `POST /api/v1/owner/ml/predictions`
- `POST /api/v1/owner/ml/predictions/auto-weather`

## Test Commands

```powershell
python -m compileall backend/app
uvicorn backend.app.main:app --reload
curl.exe -X GET "http://127.0.0.1:8000/api/v1/weather/features?stn_id=136&target_year=2025"
curl.exe -X GET "http://127.0.0.1:8000/api/v1/weather/features?stn_id=136&target_year=2026"
```

## Docs

- `docs/api/weather_feature_api.md`
- `docs/api/ml_prediction_api.md`
- `docs/api/frontend_integration_guide.md`
