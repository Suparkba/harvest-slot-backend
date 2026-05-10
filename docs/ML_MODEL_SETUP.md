# ML Model Setup

실제 ML 예측 API를 사용하려면 모델 파일을 아래 경로에 직접 배치해야 합니다.

```text
backend/app/ml_models/model.joblib
```

확인 사항:

- 파일명은 반드시 `model.joblib` 여야 합니다.
- 경로가 다르거나 파일이 없으면 `POST /api/v1/owner/ml/predictions` 호출 시 `500`과 함께 `ML model is not available`가 반환됩니다.
- 백엔드는 위 경로의 모델 파일을 lazy loading 방식으로 1회만 로드합니다.

권장 실행 순서:

1. `backend/app/ml_models/model.joblib` 파일 배치
2. `pip install -r requirements.txt`
3. `uvicorn backend.app.main:app --reload`
4. Swagger에서 `POST /api/v1/owner/ml/predictions` 테스트

실제 ML 예측을 실행하려면 `model.joblib` 파일을 `backend/app/ml_models/model.joblib` 경로에 직접 배치해야 합니다.
