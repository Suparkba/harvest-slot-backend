# Frontend Integration Guide

## Integration Options

### 1. Fetch Weather Features First

```http
GET /api/v1/weather/features?stn_id=136&target_year=2026
```

Use this when the client wants to display or confirm weather features before ML prediction.

### 2. Call Existing ML Prediction API

```http
POST /api/v1/owner/ml/predictions
```

In this flow, the client sends feature values directly in `features`.

### 3. Call Auto-Weather ML Prediction API

```http
POST /api/v1/owner/ml/predictions/auto-weather
```

In this flow, the client sends `target_year` and optional `stn_id`, and the backend generates weather features automatically.

## Important Notes For Web/App Teams

- Web and app clients do not need to know the KMA API key.
- KMA API access is a backend responsibility.
- OWNER-only APIs must include the `Authorization` header.
- `GET /api/v1/weather/features` does not require OWNER authentication in the current code.
- Default `stn_id` is Andong `136`.
