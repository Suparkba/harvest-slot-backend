# ML Prediction API

## Existing API

- Method: `POST`
- Path: `/api/v1/owner/ml/predictions`

This is the existing ML prediction API. In the original flow, web and app clients send weather feature values directly.

Required weather feature fields:

- `mar_avg_temp`
- `aug_sunshine`
- `oct_rainfall`
- `aug_humidity`

## Existing API Request Example

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

## Auto-Weather API

- Method: `POST`
- Path: `/api/v1/owner/ml/predictions/auto-weather`

This API is implemented. Web and app clients do not need to send weather feature values directly.

The backend:

1. Uses `target_year` and `stn_id`
2. Calls the weather feature logic internally
3. Generates the four weather features
4. Sends them into the existing ML prediction flow
5. Returns the prediction plus `weather_features` and `weather_source`

## Auto-Weather Request Example

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

## Web/App Choice

Clients can choose one of these approaches:

1. Call `GET /api/v1/weather/features` first, then call `POST /api/v1/owner/ml/predictions`
2. Call `POST /api/v1/owner/ml/predictions/auto-weather` once
