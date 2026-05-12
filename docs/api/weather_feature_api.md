# Weather Feature API

## API Purpose

This API lets the backend generate ML weather features so web and app clients do not need to calculate or manage weather feature values directly.

## Endpoint

- Method: `GET`
- Path: `/api/v1/weather/features`

## Query Parameters

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `stn_id` | string | no | ASOS station number. Default: `136` |
| `target_year` | integer | yes | Prediction target year |

## Default Station

- Default ASOS station: Andong `136`

## Data Source

- KMA ASOS daily weather API

## Generated Features

- `mar_avg_temp`: March average temperature, simple average of `avgTa`
- `aug_sunshine`: August sunshine total, simple sum of `sumSsHr`
- `oct_rainfall`: October rainfall total, simple sum of `sumRn`
- `aug_humidity`: August average humidity, simple average of `avgRhm`

## Fallback Policy

- If the target month data is missing, the backend falls back to the previous year.
- Fallback continues up to the previous 3 years.
- Each feature is resolved independently.
- `feature_source_years` shows the actual source year used per feature.

## 2025 Success Example

```http
GET /api/v1/weather/features?stn_id=136&target_year=2025
```

```json
{
  "data": {
    "target_year": 2025,
    "stn_id": "136",
    "mar_avg_temp": 7.42,
    "aug_sunshine": 238.8,
    "oct_rainfall": 161.6,
    "aug_humidity": 75.58,
    "source": "KMA_ASOS_DAILY_API",
    "fallback_used": false,
    "fallback_year": null,
    "fallback_reason": null,
    "feature_source_years": {
      "mar_avg_temp": 2025,
      "aug_sunshine": 2025,
      "oct_rainfall": 2025,
      "aug_humidity": 2025
    }
  },
  "message": "success",
  "error": null
}
```

## 2026 Fallback Example

```http
GET /api/v1/weather/features?stn_id=136&target_year=2026
```

```json
{
  "data": {
    "target_year": 2026,
    "stn_id": "136",
    "mar_avg_temp": 7.42,
    "aug_sunshine": 238.8,
    "oct_rainfall": 161.6,
    "aug_humidity": 75.58,
    "source": "KMA_ASOS_DAILY_API",
    "fallback_used": true,
    "fallback_year": 2025,
    "fallback_reason": "future_month_or_missing_data",
    "feature_source_years": {
      "mar_avg_temp": 2026,
      "aug_sunshine": 2025,
      "oct_rainfall": 2025,
      "aug_humidity": 2025
    }
  },
  "message": "success",
  "error": null
}
```

## Web/App Usage

- Web and app clients should call this backend API, not the KMA API directly.
- Clients do not need the KMA API key.

## Notes

- `KMA_ASOS_SERVICE_KEY` must be stored only in `.env`.
- Do not commit `.env` or any real API key to GitHub.
