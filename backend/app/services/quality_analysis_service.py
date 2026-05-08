from __future__ import annotations

from io import BytesIO

import httpx
from fastapi import HTTPException, UploadFile

from backend.app.core.config import settings
from backend.app.core.status import QualityModelDecision


VIEW_CONFIDENCE_THRESHOLD = 0.60
GRADE_CONFIDENCE_THRESHOLD = 0.55


class QualityAnalysisService:
    def analyze(self, *, image: UploadFile | None = None, image_url: str | None = None) -> dict:
        if settings.dl_quality_enabled and settings.dl_quality_api_url and image is not None:
            return self._analyze_with_external_api(image=image, image_url=image_url)
        return self._mock_result(image_url)

    def _mock_result(self, image_url: str | None) -> dict:
        return {
            "fruit_type": "apple",
            "image_url": image_url,
            "model_grade": "A",
            "freshness_score": 91.2,
            "color_score": 88.0,
            "roundness_score": 93.5,
            "bruise_probability": 0.06,
            "model_decision": QualityModelDecision.PASS,
            "action_required": "OWNER_REVIEW",
            "angle_label": "top",
            "angle_confidence": 0.92,
            "grade_confidence": 0.74,
            "view_confidence_threshold": VIEW_CONFIDENCE_THRESHOLD,
            "grade_confidence_threshold": GRADE_CONFIDENCE_THRESHOLD,
            "retake_reason": None,
            "model_version": "mock-dl-v1",
            "image_quality": {},
        }

    def _analyze_with_external_api(self, *, image: UploadFile, image_url: str | None) -> dict:
        file_name = image.filename or "quality-image.jpg"
        image.file.seek(0)
        file_bytes = image.file.read()
        image.file.seek(0)

        try:
            with httpx.Client(timeout=settings.dl_quality_timeout_seconds) as client:
                response = client.post(
                    settings.dl_quality_api_url,
                    files={
                        "image": (
                            file_name,
                            BytesIO(file_bytes),
                            image.content_type or "application/octet-stream",
                        )
                    },
                )
        except httpx.TimeoutException as exc:
            raise HTTPException(status_code=504, detail="quality analysis timeout") from exc
        except httpx.HTTPError as exc:
            raise HTTPException(status_code=502, detail="failed to analyze quality image") from exc

        try:
            payload = response.json()
        except ValueError as exc:
            raise HTTPException(status_code=502, detail="invalid quality analysis response") from exc

        if response.status_code != 200:
            raise HTTPException(status_code=502, detail="failed to analyze quality image")

        raw_data = payload.get("data", payload) if isinstance(payload, dict) else payload
        if not isinstance(raw_data, dict):
            raise HTTPException(status_code=502, detail="invalid quality analysis response")

        return self._normalize_result(raw_data, fallback_image_url=image_url)

    def _normalize_result(self, raw_data: dict, *, fallback_image_url: str | None) -> dict:
        angle_confidence = self._as_float(raw_data.get("angle_confidence"))
        grade_confidence = self._as_float(raw_data.get("grade_confidence"))

        action_required = raw_data.get("action_required") or self._derive_action_required(
            angle_confidence=angle_confidence,
            grade_confidence=grade_confidence,
        )
        model_decision = raw_data.get("model_decision") or self._derive_model_decision(action_required)

        retake_reason = raw_data.get("retake_reason")
        if action_required == "RETAKE" and not retake_reason and angle_confidence is not None:
            retake_reason = "low angle confidence"

        return {
            "fruit_type": raw_data.get("fruit_type") or "apple",
            "image_url": fallback_image_url,
            "model_grade": raw_data.get("model_grade", "A"),
            "freshness_score": self._as_float(raw_data.get("freshness_score"), 91.2),
            "color_score": self._as_float(raw_data.get("color_score"), 88.0),
            "roundness_score": self._as_float(raw_data.get("roundness_score"), 93.5),
            "bruise_probability": self._as_float(raw_data.get("bruise_probability"), 0.06),
            "model_decision": model_decision,
            "action_required": action_required,
            "angle_label": raw_data.get("angle_label"),
            "angle_confidence": angle_confidence,
            "grade_confidence": grade_confidence,
            "view_confidence_threshold": self._as_float(
                raw_data.get("view_confidence_threshold"),
                VIEW_CONFIDENCE_THRESHOLD,
            ),
            "grade_confidence_threshold": self._as_float(
                raw_data.get("grade_confidence_threshold"),
                GRADE_CONFIDENCE_THRESHOLD,
            ),
            "retake_reason": retake_reason,
            "model_version": raw_data.get("model_version", "mock-dl-v1"),
            "image_quality": raw_data.get("image_quality") or {},
        }

    def _derive_action_required(self, *, angle_confidence: float | None, grade_confidence: float | None) -> str:
        if angle_confidence is not None and angle_confidence < VIEW_CONFIDENCE_THRESHOLD:
            return "RETAKE"
        if grade_confidence is not None and grade_confidence < GRADE_CONFIDENCE_THRESHOLD:
            return "OWNER_REVIEW"
        return "OWNER_REVIEW"

    def _derive_model_decision(self, action_required: str) -> str:
        if action_required == "RETAKE":
            return "RETAKE"
        if action_required == "OWNER_REVIEW":
            return QualityModelDecision.REVIEW
        return QualityModelDecision.PASS

    def _as_float(self, value, default: float | None = None) -> float | None:
        if value is None:
            return default
        return float(value)
