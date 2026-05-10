# API Docs Overview

The files in this folder are the source of truth for the owner ML prediction API handoff.

## Share These Files

1. `docs/api/ml_prediction_api.md`
2. `docs/api/frontend_integration_guide.md`
3. `docs/api/examples/ml_prediction_request.json`
4. `docs/api/examples/ml_prediction_response.json`

## Included Files

| File | Description |
| --- | --- |
| `docs/api/ml_prediction_api.md` | Full ML prediction API spec |
| `docs/api/frontend_integration_guide.md` | Web/app integration guide |
| `docs/api/examples/ml_prediction_request.json` | Request example |
| `docs/api/examples/ml_prediction_response.json` | Success response example |
| `docs/api/examples/ml_prediction_validation_error.json` | 422 validation error example |
| `docs/api/examples/ml_prediction_auth_error.json` | 401/403 auth error examples |

## Main Endpoint

- `POST /api/v1/owner/ml/predictions`

## Notes

- Use an `OWNER` bearer token
- Keep the common response structure `{ data, message, error }`
- Place `model.joblib` at `backend/app/ml_models/model.joblib` to run real ML prediction
