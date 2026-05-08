"""
Live DL quality analysis test.

Run this test only when the backend server, Kaggle FastAPI server, and ngrok tunnel are all running.

Example:
    $env:RUN_LIVE_DL_TESTS="true"
    $env:DL_QUALITY_ENABLED="true"
    $env:DL_QUALITY_API_URL="https://xxxx.ngrok-free.app/owner/quality-inspections"
    pytest -v tests/test_live_dl_quality_api.py
"""

from __future__ import annotations

import os

import pytest


RUN_LIVE_DL_TESTS = os.getenv("RUN_LIVE_DL_TESTS", "").lower() == "true"
DL_QUALITY_API_URL = os.getenv("DL_QUALITY_API_URL", "")
DL_LIVE_IMAGE_PATH = os.getenv("DL_LIVE_IMAGE_PATH", "")

pytestmark = pytest.mark.skipif(
    not RUN_LIVE_DL_TESTS or not DL_QUALITY_API_URL or not DL_LIVE_IMAGE_PATH,
    reason="set RUN_LIVE_DL_TESTS=true, DL_QUALITY_API_URL, and DL_LIVE_IMAGE_PATH to run live DL tests",
)


def test_live_dl_quality_api_placeholder():
    assert RUN_LIVE_DL_TESTS
