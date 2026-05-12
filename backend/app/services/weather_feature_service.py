from __future__ import annotations

from calendar import monthrange
from datetime import date
import logging
from statistics import mean
from typing import Any

import httpx
from fastapi import HTTPException

from backend.app.core.config import settings


logger = logging.getLogger(__name__)
KMA_ASOS_SOURCE = "KMA_ASOS_DAILY_API"
NOT_ENOUGH_DATA_MESSAGE = "Not enough weather data to generate ML features"
NO_DATA_RESULT_CODES = {"03", "NO_DATA"}
NO_DATA_RESULT_MSG_KEYWORDS = (
    "NO_DATA",
    "NO DATA",
    "\ub370\uc774\ud130\uc5c6\uc74c",
    "\ub370\uc774\ud130 \uc5c6\uc74c",
)
KMA_FEATURE_SPECS = {
    "mar_avg_temp": {"month": 3, "field": "avgTa", "aggregation": "avg"},
    "aug_sunshine": {"month": 8, "field": "sumSsHr", "aggregation": "sum"},
    "oct_rainfall": {"month": 10, "field": "sumRn", "aggregation": "sum"},
    "aug_humidity": {"month": 8, "field": "avgRhm", "aggregation": "avg"},
}
FALLBACK_REASON = "future_month_or_missing_data"
MAX_FALLBACK_YEARS = 3


class WeatherFeatureService:
    def __init__(self) -> None:
        self._month_cache: dict[tuple[str, int, int], list[dict[str, Any]]] = {}

    def get_weather_features(self, *, target_year: int, stn_id: str | None = None) -> dict[str, Any]:
        return self.get_feature_bundle(target_year=target_year, stn_id=stn_id)

    def get_feature_bundle(self, *, target_year: int, stn_id: str | None = None) -> dict[str, Any]:
        normalized_stn_id = (stn_id or settings.kma_default_stn_id).strip()
        if not normalized_stn_id:
            normalized_stn_id = settings.kma_default_stn_id

        feature_values: dict[str, float] = {}
        feature_source_years: dict[str, int] = {}
        fallback_years_used: set[int] = set()

        for feature_name, spec in KMA_FEATURE_SPECS.items():
            resolved = self._resolve_feature_values(
                target_year=target_year,
                stn_id=normalized_stn_id,
                feature_name=feature_name,
                month=spec["month"],
                field_name=spec["field"],
            )
            if resolved is None:
                raise HTTPException(status_code=502, detail=NOT_ENOUGH_DATA_MESSAGE)

            source_year, values = resolved
            feature_values[feature_name] = self._aggregate_values(values, spec["aggregation"])
            feature_source_years[feature_name] = source_year
            if source_year != target_year:
                fallback_years_used.add(source_year)

        fallback_used = bool(fallback_years_used)
        fallback_year = max(fallback_years_used) if fallback_years_used else None

        return {
            "target_year": target_year,
            "stn_id": normalized_stn_id,
            **feature_values,
            "source": KMA_ASOS_SOURCE,
            "fallback_used": fallback_used,
            "fallback_year": fallback_year,
            "fallback_reason": FALLBACK_REASON if fallback_used else None,
            "feature_source_years": feature_source_years,
        }

    def merge_weather_features(self, features: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any] | None]:
        if self._has_complete_manual_weather_features(features):
            return features, None

        target_year = int(features.get("target_year") or self._today().year)
        stn_id = features.get("stn_id") or settings.kma_default_stn_id
        weather_bundle = self.get_weather_features(target_year=target_year, stn_id=stn_id)

        merged_features = dict(features)
        for feature_name in KMA_FEATURE_SPECS:
            merged_features[feature_name] = weather_bundle[feature_name]
        merged_features["target_year"] = target_year
        merged_features["stn_id"] = weather_bundle["stn_id"]
        return merged_features, weather_bundle

    def _has_complete_manual_weather_features(self, features: dict[str, Any]) -> bool:
        return all(features.get(feature_name) is not None for feature_name in KMA_FEATURE_SPECS)

    def _resolve_feature_values(
        self,
        *,
        target_year: int,
        stn_id: str,
        feature_name: str,
        month: int,
        field_name: str,
    ) -> tuple[int, list[float]] | None:
        for year_offset in range(0, MAX_FALLBACK_YEARS + 1):
            candidate_year = target_year - year_offset
            if year_offset == 0 and self._is_future_month(candidate_year, month):
                logger.info(
                    "Skipping future month and moving to fallback: feature=%s stn_id=%s year=%s month=%s",
                    feature_name,
                    stn_id,
                    candidate_year,
                    month,
                )
                continue

            rows = self._fetch_month_rows(target_year=candidate_year, month=month, stn_id=stn_id)
            values = self._extract_numeric_values(rows=rows, field_name=field_name)
            if values:
                return candidate_year, values

            logger.info(
                "KMA ASOS returned no usable rows for feature=%s stn_id=%s year=%s month=%s field=%s",
                feature_name,
                stn_id,
                candidate_year,
                month,
                field_name,
            )
        return None

    def _fetch_month_rows(self, *, target_year: int, month: int, stn_id: str) -> list[dict[str, Any]]:
        cache_key = (stn_id, target_year, month)
        if cache_key in self._month_cache:
            return self._month_cache[cache_key]

        last_day = monthrange(target_year, month)[1]
        rows = self._request_asos_rows(
            start_date=f"{target_year}{month:02d}01",
            end_date=f"{target_year}{month:02d}{last_day:02d}",
            stn_id=stn_id,
        )
        self._month_cache[cache_key] = rows
        return rows

    def _request_asos_rows(self, *, start_date: str, end_date: str, stn_id: str) -> list[dict[str, Any]]:
        service_key = (settings.kma_asos_service_key or "").strip()
        base_url = settings.kma_asos_base_url.strip()
        if not service_key:
            raise HTTPException(status_code=500, detail="KMA_ASOS_SERVICE_KEY is not configured")
        if not base_url:
            raise HTTPException(status_code=500, detail="KMA_ASOS_BASE_URL is not configured")

        params = {
            "ServiceKey": service_key,
            "pageNo": 1,
            "numOfRows": 100,
            "dataType": "JSON",
            "dataCd": "ASOS",
            "dateCd": "DAY",
            "startDt": start_date,
            "endDt": end_date,
            "stnIds": stn_id,
        }

        try:
            with httpx.Client(timeout=settings.kma_asos_timeout_seconds) as client:
                response = client.get(base_url, params=params)
        except HTTPException:
            raise
        except httpx.HTTPError as exc:
            logger.exception(
                "KMA ASOS request failed: stn_id=%s startDt=%s endDt=%s error=%s",
                stn_id,
                start_date,
                end_date,
                exc,
            )
            raise HTTPException(status_code=502, detail="failed to fetch weather data from KMA ASOS API") from exc
        except Exception as exc:
            logger.exception(
                "Unexpected KMA ASOS request error: stn_id=%s startDt=%s endDt=%s error=%s",
                stn_id,
                start_date,
                end_date,
                exc,
            )
            raise HTTPException(status_code=502, detail="failed to fetch weather data from KMA ASOS API") from exc

        if response.status_code != 200:
            logger.error(
                "KMA ASOS non-200 response: stn_id=%s startDt=%s endDt=%s status=%s body=%s",
                stn_id,
                start_date,
                end_date,
                response.status_code,
                response.text[:500],
            )
            raise HTTPException(status_code=502, detail="failed to fetch weather data from KMA ASOS API")

        try:
            payload = response.json()
        except ValueError as exc:
            logger.exception(
                "KMA ASOS JSON decode failed: stn_id=%s startDt=%s endDt=%s body=%s",
                stn_id,
                start_date,
                end_date,
                response.text[:500],
            )
            raise HTTPException(status_code=502, detail="invalid KMA ASOS API response") from exc

        response_payload = payload.get("response") or {}
        header = response_payload.get("header") or {}
        body = response_payload.get("body") or {}
        result_code = str(header.get("resultCode") or "")
        result_msg = str(header.get("resultMsg") or "")

        if result_code == "00":
            items_container = body.get("items") or {}
            items = items_container.get("item")
            if isinstance(items, dict):
                return [items]
            if isinstance(items, list):
                return items
            logger.info(
                "KMA ASOS returned empty item list: stn_id=%s startDt=%s endDt=%s resultCode=%s resultMsg=%s body=%s",
                stn_id,
                start_date,
                end_date,
                result_code,
                result_msg,
                response.text[:500],
            )
            return []

        if self._is_no_data_result(result_code=result_code, result_msg=result_msg):
            logger.info(
                "KMA ASOS returned no-data result: stn_id=%s startDt=%s endDt=%s resultCode=%s resultMsg=%s body=%s",
                stn_id,
                start_date,
                end_date,
                result_code,
                result_msg,
                response.text[:500],
            )
            return []

        logger.error(
            "KMA ASOS business error: stn_id=%s startDt=%s endDt=%s resultCode=%s resultMsg=%s body=%s",
            stn_id,
            start_date,
            end_date,
            result_code,
            result_msg,
            response.text[:500],
        )
        raise HTTPException(status_code=502, detail="failed to fetch weather data from KMA ASOS API")

    def _extract_numeric_values(self, *, rows: list[dict[str, Any]], field_name: str) -> list[float]:
        values: list[float] = []
        for row in rows:
            raw_value = row.get(field_name)
            if field_name == "sumRn" and raw_value == "":
                values.append(0.0)
                continue
            if raw_value in {None, ""}:
                continue
            try:
                values.append(float(raw_value))
            except (TypeError, ValueError):
                continue
        return values

    def _aggregate_values(self, values: list[float], aggregation: str) -> float:
        if aggregation == "sum":
            return round(sum(values), 2)
        return round(mean(values), 2)

    def _today(self) -> date:
        return date.today()

    def _is_future_month(self, year: int, month: int) -> bool:
        today = self._today()
        return (year, month) > (today.year, today.month)

    def _is_no_data_result(self, *, result_code: str, result_msg: str) -> bool:
        normalized_code = result_code.strip().upper()
        normalized_msg = result_msg.strip().upper()
        if normalized_code in NO_DATA_RESULT_CODES:
            return True
        return any(keyword in normalized_msg for keyword in NO_DATA_RESULT_MSG_KEYWORDS)
