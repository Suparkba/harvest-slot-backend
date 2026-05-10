# Frontend Integration Guide

This guide is for web/app teams integrating the owner ML prediction API.

## API Summary

- Method: `POST`
- Path: `/api/v1/owner/ml/predictions`
- Auth: `Authorization: Bearer {access_token}`
- Content-Type: `application/json`

## Recommended UI Fields

- `estimated_yield_kg`
- `suggested_reservable_min_kg`
- `suggested_reservable_max_kg`
- `recommended_price`
- `predicted_harvest_start`
- `predicted_harvest_end`
- `warning_message`

## Request Example

```http
POST /api/v1/owner/ml/predictions
Authorization: Bearer {access_token}
Content-Type: application/json
```

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

## Response Example

```json
{
  "data": {
    "prediction_id": 1,
    "farm_id": 1,
    "product_id": 1,
    "unit_yield_kg_10a": 1509.54,
    "predicted_harvest_start": "YYYY-MM-DD",
    "predicted_harvest_end": "YYYY-MM-DD",
    "estimated_yield_kg": 3019.08,
    "suggested_reservable_min_kg": 1207.63,
    "suggested_reservable_max_kg": 2264.31,
    "recommended_price": 5000,
    "confidence": 0.78,
    "safety_factor": 0.75,
    "warning_message": "정상",
    "model_version": "rf-apple-harvest-v1"
  },
  "message": "success",
  "error": null
}
```

## Integration Notes

- The API keeps the common response wrapper: `{ data, message, error }`
- Validation errors return HTTP `422`
- Missing or invalid token returns `401`
- Non-owner access returns `403`
- `recommended_price` is returned as an integer
- `predicted_harvest_start` and `predicted_harvest_end` are date strings

## Display Recommendation

Show these values prominently on the prediction result screen:

- Estimated total yield
- Reservable minimum kg
- Reservable maximum kg
- Recommended price
- Harvest start date
- Harvest end date
- Warning/status message

## Backend Runtime Note

`model.joblib` and the `scikit-learn` version are managed only in the backend runtime. Web/app clients do not need any separate handling beyond calling the API.
