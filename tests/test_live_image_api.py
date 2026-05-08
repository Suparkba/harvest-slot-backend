"""
Live image upload API tests.

Run these tests only after starting the FastAPI server and enabling live tests.

Example:
    uvicorn backend.app.main:app --reload
    $env:RUN_LIVE_IMAGE_TESTS="true"
    pytest -v tests/test_live_image_api.py

These tests send real HTTP requests and may call the NAS image upload API.
"""

from __future__ import annotations

import os
from uuid import uuid4

import httpx
import pytest


BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8000/api/v1")
TIMEOUT = 30.0
RUN_LIVE_IMAGE_TESTS = os.getenv("RUN_LIVE_IMAGE_TESTS", "").lower() == "true"

pytestmark = pytest.mark.skipif(
    not RUN_LIVE_IMAGE_TESTS,
    reason="set RUN_LIVE_IMAGE_TESTS=true to run live image upload tests",
)


def _request(
    client: httpx.Client,
    method: str,
    path: str,
    *,
    expected_status: int,
    step: str,
    headers: dict[str, str] | None = None,
    files: dict | None = None,
    json: dict | None = None,
) -> dict:
    url = f"{BASE_URL}{path}"
    try:
        response = client.request(method, url, headers=headers, files=files, json=json)
    except httpx.ConnectError as exc:
        raise AssertionError(
            f"{step}: live server connection failed. Start uvicorn first and verify BASE_URL={BASE_URL}"
        ) from exc
    except httpx.HTTPError as exc:
        raise AssertionError(f"{step}: live HTTP request failed for {url}: {exc}") from exc

    assert (
        response.status_code == expected_status
    ), f"{step}: expected {expected_status}, got {response.status_code}, body={response.text}"
    return response.json()


def _owner_headers(client: httpx.Client) -> dict[str, str]:
    body = _request(
        client,
        "POST",
        "/auth/login",
        expected_status=200,
        step="owner login",
        json={"email": "owner@test.com", "password": "demo1234!"},
    )
    token = body["data"]["access_token"]
    assert token, "owner login: access_token is missing"
    return {"Authorization": f"Bearer {token}"}


def test_live_owner_image_upload_endpoints():
    with httpx.Client(timeout=TIMEOUT) as client:
        headers = _owner_headers(client)

        product_upload = _request(
            client,
            "POST",
            "/owner/products/1/image",
            expected_status=200,
            step="product image upload",
            headers=headers,
            files={
                "file": (
                    f"live-product-{uuid4().hex[:8]}.jpg",
                    b"live-product-image",
                    "image/jpeg",
                )
            },
        )
        assert product_upload["data"]["image_url"], "product image upload: image_url missing"

        quality_upload = _request(
            client,
            "POST",
            "/owner/quality-inspections/image",
            expected_status=200,
            step="quality image upload",
            headers=headers,
            files={
                "file": (
                    f"live-quality-{uuid4().hex[:8]}.jpg",
                    b"live-quality-image",
                    "image/jpeg",
                )
            },
        )
        assert quality_upload["data"]["image_url"], "quality image upload: image_url missing"
