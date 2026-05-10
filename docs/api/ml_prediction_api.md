# ML Prediction API

## Purpose

This API lets an owner submit farm/product context plus manual input features and receive an ML-based apple harvest prediction.

## Authorization

- Role: `OWNER`
- Header: `Authorization: Bearer {access_token}`

## Endpoint

- Method: `POST`
- Path: `/api/v1/owner/ml/predictions`
- Content-Type: `application/json`

## Request

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

## Request Fields

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `farm_id` | integer | yes | Owner farm id |
| `product_id` | integer | yes | Product id under the farm |
| `features` | object | yes | ML feature bundle |

### `features`

| Field | Type | Validation | Notes |
| --- | --- | --- | --- |
| `past_yield_kg` | number | `gt=0` | Historical harvest yield in kg |
| `market_price` | number | `gt=0` | Current market price |
| `variety` | string | `min_length=1` | Example: `부사` |
| `mar_avg_temp` | number | `-5 <= x <= 25` | March average temperature |
| `aug_sunshine` | number | `50 <= x <= 400` | August sunshine hours |
| `oct_rainfall` | number | `0 <= x <= 600` | October rainfall |
| `aug_humidity` | number | `30 <= x <= 100` | August humidity |

## Response

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

## Response Fields

| Field | Type | Notes |
| --- | --- | --- |
| `prediction_id` | integer | Prediction id |
| `farm_id` | integer | Farm id |
| `product_id` | integer | Product id |
| `unit_yield_kg_10a` | number | ML model output for 10a harvest yield |
| `predicted_harvest_start` | string | `YYYY-MM-DD` |
| `predicted_harvest_end` | string | `YYYY-MM-DD` |
| `estimated_yield_kg` | number | Adjusted estimated yield |
| `suggested_reservable_min_kg` | number | Minimum reservable recommendation |
| `suggested_reservable_max_kg` | number | Maximum reservable recommendation |
| `recommended_price` | integer | Suggested price |
| `confidence` | number | Static confidence value |
| `safety_factor` | number | Static safety factor |
| `warning_message` | string | Display-ready warning/status text |
| `model_version` | string | Current ML model version |

## Error Examples

### 422 Validation Error

```json
{
  "data": {},
  "message": "validation failed",
  "error": [
    {
      "type": "less_than_equal",
      "loc": ["body", "features", "aug_humidity"],
      "msg": "Input should be less than or equal to 100",
      "input": 120,
      "ctx": {
        "le": 100.0
      }
    }
  ]
}
```

### 401 Authentication Required

```json
{
  "data": {},
  "message": "authentication required",
  "error": "authentication required"
}
```

### 403 Forbidden

```json
{
  "data": {},
  "message": "forbidden",
  "error": "forbidden"
}
```

## UI Recommendation

Recommended fields for web/app result screens:

- `estimated_yield_kg`
- `suggested_reservable_min_kg`
- `suggested_reservable_max_kg`
- `recommended_price`
- `predicted_harvest_start`
- `predicted_harvest_end`
- `warning_message`

## Swagger Test

1. Run the server with `uvicorn backend.app.main:app --reload`
2. Open `http://127.0.0.1:8000/docs`
3. Authorize with an `OWNER` bearer token
4. Call `POST /api/v1/owner/ml/predictions`
5. Use the request example in this document

## Model File Placement

실제 ML 예측을 실행하려면 `model.joblib` 파일을 `backend/app/ml_models/model.joblib` 경로에 직접 배치해야 합니다.
