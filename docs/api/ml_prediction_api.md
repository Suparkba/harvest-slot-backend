# ML 예측 API

## 기존 API

- Method: `POST`
- Path: `/api/v1/owner/ml/predictions`

기존 ML 예측 API입니다. 기본 방식은 앱/웹이 날씨 피처값을 직접 `features`에 넣어서 호출하는 방식입니다.

필수 날씨 피처:

- `mar_avg_temp`
- `aug_sunshine`
- `oct_rainfall`
- `aug_humidity`

## 기존 API 요청 예시

```json
{
  "farm_id": 1,
  "product_id": 1,
  "features": {
    "past_yield_kg": 3000,
    "market_price": 5000,
    "variety": "부사",
    "mar_avg_temp": 7.42,
    "aug_sunshine": 238.8,
    "oct_rainfall": 161.6,
    "aug_humidity": 75.58
  }
}
```

## 자동 날씨 예측 API

- Method: `POST`
- Path: `/api/v1/owner/ml/predictions/auto-weather`

이 API는 구현되어 있습니다. 앱/웹이 날씨 피처값을 직접 넣지 않아도 됩니다.

백엔드는 아래 순서로 동작합니다.

1. `target_year`와 `stn_id`를 기준으로 날씨 피처를 생성합니다.
2. 생성된 4개 피처를 기존 ML 예측 로직에 전달합니다.
3. 예측 결과와 함께 `weather_features`, `weather_source`를 반환합니다.

## 자동 날씨 예측 API 요청 예시

```json
{
  "farm_id": 1,
  "product_id": 1,
  "target_year": 2026,
  "stn_id": "136",
  "past_yield_kg": 3000,
  "market_price": 5000,
  "variety": "부사"
}
```

## 앱/웹 선택 방식

앱/웹은 아래 두 방식 중 하나를 선택할 수 있습니다.

1. `GET /api/v1/weather/features` 호출 후 `POST /api/v1/owner/ml/predictions` 호출
2. `POST /api/v1/owner/ml/predictions/auto-weather` 한 번만 호출
