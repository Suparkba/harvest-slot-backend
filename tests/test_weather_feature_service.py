from datetime import date

import httpx
import pytest
from fastapi import HTTPException

from backend.app.core.config import settings
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


@pytest.fixture(autouse=True)
def fixed_today(monkeypatch):
    monkeypatch.setattr(WeatherFeatureService, "_today", lambda self: date(2026, 5, 12))


def test_service_uses_feature_level_fallback(monkeypatch):
    monkeypatch.setattr(settings, "kma_asos_service_key", "dummy-key")
    monkeypatch.setattr(settings, "kma_asos_base_url", "http://dummy.test/asos")
    monkeypatch.setattr(settings, "kma_default_stn_id", "136")

    responses = {
        "202603": DummyResponse(_build_asos_response([{"tm": "2026-03-01", "avgTa": "7.42"}])),
        "202508": DummyResponse(_build_asos_response([{"tm": "2025-08-01", "sumSsHr": "238.8", "avgRhm": "75.58"}])),
        "202510": DummyResponse(_build_asos_response([{"tm": "2025-10-01", "sumRn": "161.6"}])),
    }
    monkeypatch.setattr(httpx, "Client", lambda *args, **kwargs: DummyWeatherClient(responses))

    data = WeatherFeatureService().get_weather_features(target_year=2026, stn_id="136")

    assert data["fallback_used"] is True
    assert data["fallback_year"] == 2025
    assert data["feature_source_years"] == {
        "mar_avg_temp": 2026,
        "aug_sunshine": 2025,
        "oct_rainfall": 2025,
        "aug_humidity": 2025,
    }


def test_service_raises_clear_error_when_all_fallbacks_fail(monkeypatch):
    monkeypatch.setattr(settings, "kma_asos_service_key", "dummy-key")
    monkeypatch.setattr(settings, "kma_asos_base_url", "http://dummy.test/asos")
    monkeypatch.setattr(settings, "kma_default_stn_id", "136")

    responses = {
        "202603": DummyResponse(_build_asos_response([])),
        "202503": DummyResponse(_build_asos_response([])),
        "202403": DummyResponse(_build_asos_response([])),
        "202303": DummyResponse(_build_asos_response([])),
    }
    monkeypatch.setattr(httpx, "Client", lambda *args, **kwargs: DummyWeatherClient(responses))

    with pytest.raises(HTTPException) as exc_info:
        WeatherFeatureService().get_weather_features(target_year=2026, stn_id="136")

    assert exc_info.value.status_code == 502
    assert exc_info.value.detail == "Not enough weather data to generate ML features"
