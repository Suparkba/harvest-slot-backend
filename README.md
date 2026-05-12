# Harvest Slot 백엔드

Harvest Slot 프로젝트용 FastAPI 백엔드입니다.

## 실행 방법

```powershell
pip install -r requirements.txt
$env:PYTHONPATH = (Get-Location).Path
uvicorn backend.app.main:app --reload
```

## 기본 실행 정보

- 앱 진입점: `backend.app.main:app`
- API prefix: `/api/v1`
- Swagger 문서: `http://127.0.0.1:8000/docs`
- ML 모델 경로: `backend/app/ml_models/model.joblib`

## KMA ASOS 환경변수

`.env.example`에는 빈 키 값만 유지해야 합니다.

```env
KMA_ASOS_SERVICE_KEY=
KMA_ASOS_BASE_URL=http://apis.data.go.kr/1360000/AsosDalyInfoService/getWthrDataList
KMA_DEFAULT_STN_ID=136
```

주의사항:

- 실제 `KMA_ASOS_SERVICE_KEY`는 `.env`에만 넣습니다.
- `.env`는 Git에 올리면 안 됩니다.
- `.env.example`에는 실제 키를 넣지 않습니다.

## 주요 API

- `GET /api/v1/weather/features`
- `POST /api/v1/owner/ml/predictions`
- `POST /api/v1/owner/ml/predictions/auto-weather`

## 테스트 명령어

```powershell
python -m compileall backend/app
uvicorn backend.app.main:app --reload
curl.exe -X GET "http://127.0.0.1:8000/api/v1/weather/features?stn_id=136&target_year=2025"
curl.exe -X GET "http://127.0.0.1:8000/api/v1/weather/features?stn_id=136&target_year=2026"
```

## 문서

- `docs/api/weather_feature_api.md`
- `docs/api/ml_prediction_api.md`
- `docs/api/frontend_integration_guide.md`
