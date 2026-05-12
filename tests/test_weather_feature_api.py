from datetime import date

import httpx
import pytest

from backend.app.core.config import settings
from backend.app.services import ml_service
from backend.app.services.weather_feature_service import WeatherFeatureService


class DummyResponse:
    def __init__(self, payload, status_code: int = 200, text: str | None = None):
        self._payload = payload
        self.status_code = status_code
        self.text = text or str(payload)

    def json(self):
        return self._payload


class DummyWeatherClient:
    def __init__(self, responses_by_period: dict[str, DummyResponse]):
        self.responses_by_period = responses_by_period

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def get(self, url, params=None):
        period = str(params["startDt"])[:6]
        return self.responses_by_period[period]


def _build_asos_response(items):
    return {
        "response": {
            "header": {"resultCode": "00", "resultMsg": "NORMAL_SERVICE"},
            "body": {"items": {"item": items}},
        }
    }


def _build_asos_no_data_response(result_code="03", result_msg="NO_DATA"):
    return {
        "response": {
            "header": {"resultCode": result_code, "resultMsg": result_msg},
            "body": {"items": {}},
        }
    }


@pytest.fixture(autouse=True)
def fixed_today(monkeypatch):
    monkeypatch.setattr(WeatherFeatureService, "_today", lambda self: date(2026, 5, 12))


def test_weather_features_endpoint_uses_target_year_data_when_available(client, monkeypatch):
    monkeypatch.setattr(settings, "kma_asos_service_key", "dummy-key")
    monkeypatch.setattr(settings, "kma_asos_base_url", "http://dummy.test/asos")
    monkeypatch.setattr(settings, "kma_default_stn_id", "136")

    responses = {
        "202503": DummyResponse(_build_asos_response([{"tm": "2025-03-01", "avgTa": "5.8"}, {"tm": "2025-03-02", "avgTa": "6.2"}])),
        "202508": DummyResponse(
            _build_asos_response(
                [
                    {"tm": "2025-08-01", "sumSsHr": "120.0", "avgRhm": "70.0"},
                    {"tm": "2025-08-02", "sumSsHr": "130.0", "avgRhm": "74.0"},
                ]
            )
        ),
        "202510": DummyResponse(_build_asos_response([{"tm": "2025-10-01", "sumRn": "10.0"}, {"tm": "2025-10-02", "sumRn": "15.0"}])),
    }
    monkeypatch.setattr(httpx, "Client", lambda *args, **kwargs: DummyWeatherClient(responses))

    response = client.get("/api/v1/weather/features", params={"stn_id": "136", "target_year": 2025})

    assert response.status_code == 200
    assert response.json()["data"] == {
        "target_year": 2025,
        "stn_id": "136",
        "mar_avg_temp": 6.0,
        "aug_sunshine": 250.0,
        "oct_rainfall": 25.0,
        "aug_humidity": 72.0,
        "source": "KMA_ASOS_DAILY_API",
        "fallback_used": False,
        "fallback_year": None,
        "fallback_reason": None,
        "feature_source_years": {
            "mar_avg_temp": 2025,
            "aug_sunshine": 2025,
            "oct_rainfall": 2025,
            "aug_humidity": 2025,
        },
    }


def test_weather_features_endpoint_returns_aggregated_values_with_fallback(client, monkeypatch):
    monkeypatch.setattr(settings, "kma_asos_service_key", "dummy-key")
    monkeypatch.setattr(settings, "kma_asos_base_url", "http://dummy.test/asos")
    monkeypatch.setattr(settings, "kma_default_stn_id", "136")

    responses = {
        "202603": DummyResponse(_build_asos_response([{"tm": "2026-03-01", "avgTa": "8.0"}, {"tm": "2026-03-02", "avgTa": "9.0"}])),
        "202608": DummyResponse(_build_asos_response([])),
        "202610": DummyResponse(_build_asos_response([])),
        "202508": DummyResponse(
            _build_asos_response(
                [
                    {"tm": "2025-08-01", "sumSsHr": "100.0", "avgRhm": "70.0"},
                    {"tm": "2025-08-02", "sumSsHr": "110.0", "avgRhm": "74.0"},
                ]
            )
        ),
        "202510": DummyResponse(_build_asos_response([{"tm": "2025-10-01", "sumRn": ""}, {"tm": "2025-10-02", "sumRn": "35.0"}])),
    }
    monkeypatch.setattr(httpx, "Client", lambda *args, **kwargs: DummyWeatherClient(responses))

    response = client.get("/api/v1/weather/features", params={"stn_id": "136", "target_year": 2026})

    assert response.status_code == 200
    assert response.json()["data"] == {
        "target_year": 2026,
        "stn_id": "136",
        "mar_avg_temp": 8.5,
        "aug_sunshine": 210.0,
        "oct_rainfall": 35.0,
        "aug_humidity": 72.0,
        "source": "KMA_ASOS_DAILY_API",
        "fallback_used": True,
        "fallback_year": 2025,
        "fallback_reason": "future_month_or_missing_data",
        "feature_source_years": {
            "mar_avg_temp": 2026,
            "aug_sunshine": 2025,
            "oct_rainfall": 2025,
            "aug_humidity": 2025,
        },
    }


def test_weather_features_endpoint_returns_clear_error_without_api_key(client, monkeypatch):
    monkeypatch.setattr(settings, "kma_asos_service_key", None)

    response = client.get("/api/v1/weather/features", params={"target_year": 2026})

    assert response.status_code == 500
    body = response.json()
    assert body["message"] == "KMA_ASOS_SERVICE_KEY is not configured"
    assert body["error"] == "KMA_ASOS_SERVICE_KEY is not configured"


def test_owner_ml_prediction_auto_fills_weather_features(client, monkeypatch):
    class DummyModel:
        def predict(self, input_df):
            assert list(input_df.columns) == ml_service.FEATURES
            assert input_df.iloc[0].to_dict() == {
                "mar_avg_temp": 8.5,
                "aug_sunshine": 210.0,
                "oct_rainfall": 35.0,
                "aug_humidity": 72.0,
            }
            return [1509.53]

    monkeypatch.setattr(settings, "kma_asos_service_key", "dummy-key")
    monkeypatch.setattr(settings, "kma_asos_base_url", "http://dummy.test/asos")
    monkeypatch.setattr(settings, "kma_default_stn_id", "136")
    monkeypatch.setattr(ml_service, "get_ml_model", lambda: DummyModel())

    responses = {
        "202603": DummyResponse(_build_asos_response([{"tm": "2026-03-01", "avgTa": "8.0"}, {"tm": "2026-03-02", "avgTa": "9.0"}])),
        "202608": DummyResponse(_build_asos_response([])),
        "202610": DummyResponse(_build_asos_response([])),
        "202508": DummyResponse(
            _build_asos_response(
                [
                    {"tm": "2025-08-01", "sumSsHr": "100.0", "avgRhm": "70.0"},
                    {"tm": "2025-08-02", "sumSsHr": "110.0", "avgRhm": "74.0"},
                ]
            )
        ),
        "202510": DummyResponse(_build_asos_response([{"tm": "2025-10-01", "sumRn": ""}, {"tm": "2025-10-02", "sumRn": "35.0"}])),
    }
    monkeypatch.setattr(httpx, "Client", lambda *args, **kwargs: DummyWeatherClient(responses))

    payload = {
        "farm_id": 1,
        "product_id": 1,
        "features": {
            "past_yield_kg": 3000,
            "market_price": 5000,
            "variety": "부사",
            "target_year": 2026,
            "stn_id": "136",
        },
    }
    response = client.post(
        "/api/v1/owner/ml/predictions",
        json=payload,
        headers={"Authorization": "Bearer mock-owner-token"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["data"]["prediction_id"] >= 1
    assert body["data"]["unit_yield_kg_10a"] == 1509.53


def test_owner_ml_prediction_auto_weather_endpoint_returns_weather_metadata(client, monkeypatch):
    class DummyModel:
        def predict(self, input_df):
            assert list(input_df.columns) == ml_service.FEATURES
            return [1509.53]

    monkeypatch.setattr(settings, "kma_asos_service_key", "dummy-key")
    monkeypatch.setattr(settings, "kma_asos_base_url", "http://dummy.test/asos")
    monkeypatch.setattr(settings, "kma_default_stn_id", "136")
    monkeypatch.setattr(ml_service, "get_ml_model", lambda: DummyModel())

    responses = {
        "202603": DummyResponse(_build_asos_response([{"tm": "2026-03-01", "avgTa": "7.42"}])),
        "202508": DummyResponse(_build_asos_response([{"tm": "2025-08-01", "sumSsHr": "238.8", "avgRhm": "75.58"}])),
        "202510": DummyResponse(_build_asos_response([{"tm": "2025-10-01", "sumRn": "161.6"}])),
    }
    monkeypatch.setattr(httpx, "Client", lambda *args, **kwargs: DummyWeatherClient(responses))

    payload = {
        "farm_id": 1,
        "product_id": 1,
        "target_year": 2026,
        "stn_id": "136",
        "past_yield_kg": 3000,
        "market_price": 5000,
        "variety": "부사",
    }
    response = client.post(
        "/api/v1/owner/ml/predictions/auto-weather",
        json=payload,
        headers={"Authorization": "Bearer mock-owner-token"},
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["prediction_id"] >= 1
    assert data["weather_features"] == {
        "mar_avg_temp": 7.42,
        "aug_sunshine": 238.8,
        "oct_rainfall": 161.6,
        "aug_humidity": 75.58,
    }
    assert data["weather_source"] == {
        "source": "KMA_ASOS_DAILY_API",
        "fallback_used": True,
        "fallback_year": 2025,
        "fallback_reason": "future_month_or_missing_data",
        "feature_source_years": {
            "mar_avg_temp": 2026,
            "aug_sunshine": 2025,
            "oct_rainfall": 2025,
            "aug_humidity": 2025,
        },
    }


def test_weather_features_endpoint_falls_back_up_to_three_years(client, monkeypatch):
    monkeypatch.setattr(settings, "kma_asos_service_key", "dummy-key")
    monkeypatch.setattr(settings, "kma_asos_base_url", "http://dummy.test/asos")
    monkeypatch.setattr(settings, "kma_default_stn_id", "136")

    responses = {
        "202603": DummyResponse(_build_asos_response([])),
        "202608": DummyResponse(_build_asos_response([])),
        "202610": DummyResponse(_build_asos_response([])),
        "202503": DummyResponse(_build_asos_response([])),
        "202508": DummyResponse(_build_asos_response([])),
        "202510": DummyResponse(_build_asos_response([])),
        "202403": DummyResponse(_build_asos_response([{"tm": "2024-03-01", "avgTa": "7.0"}, {"tm": "2024-03-02", "avgTa": "9.0"}])),
        "202408": DummyResponse(_build_asos_response([{"tm": "2024-08-01", "sumSsHr": "120.0", "avgRhm": "68.0"}, {"tm": "2024-08-02", "sumSsHr": "100.0", "avgRhm": "72.0"}])),
        "202410": DummyResponse(_build_asos_response([{"tm": "2024-10-01", "sumRn": "20.0"}, {"tm": "2024-10-02", "sumRn": "25.0"}])),
    }
    monkeypatch.setattr(httpx, "Client", lambda *args, **kwargs: DummyWeatherClient(responses))

    response = client.get("/api/v1/weather/features", params={"target_year": 2026})

    assert response.status_code == 200
    body = response.json()
    assert body["data"]["stn_id"] == "136"
    assert body["data"]["fallback_used"] is True
    assert body["data"]["fallback_year"] == 2024
    assert body["data"]["feature_source_years"] == {
        "mar_avg_temp": 2024,
        "aug_sunshine": 2024,
        "oct_rainfall": 2024,
        "aug_humidity": 2024,
    }


def test_weather_features_endpoint_treats_no_data_code_as_fallbackable_empty_result(client, monkeypatch):
    monkeypatch.setattr(settings, "kma_asos_service_key", "dummy-key")
    monkeypatch.setattr(settings, "kma_asos_base_url", "http://dummy.test/asos")
    monkeypatch.setattr(settings, "kma_default_stn_id", "136")

    responses = {
        "202603": DummyResponse(_build_asos_no_data_response()),
        "202608": DummyResponse(_build_asos_no_data_response()),
        "202610": DummyResponse(_build_asos_no_data_response()),
        "202503": DummyResponse(_build_asos_response([{"tm": "2025-03-01", "avgTa": "5.8"}, {"tm": "2025-03-02", "avgTa": "6.2"}])),
        "202508": DummyResponse(_build_asos_response([{"tm": "2025-08-01", "sumSsHr": "100.0", "avgRhm": "70.0"}, {"tm": "2025-08-02", "sumSsHr": "110.0", "avgRhm": "74.0"}])),
        "202510": DummyResponse(_build_asos_response([{"tm": "2025-10-01", "sumRn": "30.0"}, {"tm": "2025-10-02", "sumRn": "35.0"}])),
    }
    monkeypatch.setattr(httpx, "Client", lambda *args, **kwargs: DummyWeatherClient(responses))

    response = client.get("/api/v1/weather/features", params={"stn_id": "136", "target_year": 2026})

    assert response.status_code == 200
    assert response.json()["data"]["feature_source_years"] == {
        "mar_avg_temp": 2025,
        "aug_sunshine": 2025,
        "oct_rainfall": 2025,
        "aug_humidity": 2025,
    }


def test_weather_features_endpoint_returns_not_enough_data_after_all_fallbacks_fail(client, monkeypatch):
    monkeypatch.setattr(settings, "kma_asos_service_key", "dummy-key")
    monkeypatch.setattr(settings, "kma_asos_base_url", "http://dummy.test/asos")
    monkeypatch.setattr(settings, "kma_default_stn_id", "136")

    responses = {
        "202603": DummyResponse(_build_asos_no_data_response()),
        "202608": DummyResponse(_build_asos_no_data_response()),
        "202610": DummyResponse(_build_asos_no_data_response()),
        "202503": DummyResponse(_build_asos_no_data_response(result_msg="NO_DATA")),
        "202508": DummyResponse(_build_asos_no_data_response(result_msg="데이터없음")),
        "202510": DummyResponse(_build_asos_no_data_response(result_msg="NO_DATA")),
        "202403": DummyResponse(_build_asos_response([])),
        "202408": DummyResponse(_build_asos_response([])),
        "202410": DummyResponse(_build_asos_response([])),
        "202303": DummyResponse(_build_asos_response([])),
        "202308": DummyResponse(_build_asos_response([])),
        "202310": DummyResponse(_build_asos_response([])),
    }
    monkeypatch.setattr(httpx, "Client", lambda *args, **kwargs: DummyWeatherClient(responses))

    response = client.get("/api/v1/weather/features", params={"stn_id": "136", "target_year": 2026})

    assert response.status_code == 502
    body = response.json()
    assert body["message"] == "Not enough weather data to generate ML features"
    assert body["error"] == "Not enough weather data to generate ML features"


def test_weather_features_endpoint_accepts_single_item_dict(client, monkeypatch):
    monkeypatch.setattr(settings, "kma_asos_service_key", "  dummy-key  ")
    monkeypatch.setattr(settings, "kma_asos_base_url", "http://dummy.test/asos")
    monkeypatch.setattr(settings, "kma_default_stn_id", "136")

    responses = {
        "202603": DummyResponse(_build_asos_response({"tm": "2026-03-01", "avgTa": "8.0"})),
        "202608": DummyResponse(_build_asos_response([])),
        "202610": DummyResponse(_build_asos_response([])),
        "202508": DummyResponse(_build_asos_response([{"tm": "2025-08-01", "sumSsHr": "120.0", "avgRhm": "71.0"}])),
        "202510": DummyResponse(_build_asos_response([{"tm": "2025-10-01", "sumRn": "10.0"}])),
    }
    captured_params: list[dict] = []

    class CapturingWeatherClient(DummyWeatherClient):
        def get(self, url, params=None):
            captured_params.append(params)
            return super().get(url, params=params)

    monkeypatch.setattr(httpx, "Client", lambda *args, **kwargs: CapturingWeatherClient(responses))

    response = client.get("/api/v1/weather/features", params={"target_year": 2026})

    assert response.status_code == 200
    assert captured_params[0]["ServiceKey"] == "dummy-key"
    assert captured_params[0]["stnIds"] == "136"
