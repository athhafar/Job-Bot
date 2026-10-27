"""Unit tests for Meta Threads API source with mocked responses (no real API calls)."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
import pytest

from core.threads_token import ThreadsTokenManager
from sources.threads import ThreadsAPIError, ThreadsSource, mask_secret


@pytest.fixture
def sample_threads_json():
    return {
        "data": [
            {
                "id": "18012345678901234",
                "text": "Kami sedang butuh Flutter developer untuk proyek aplikasi e-commerce 3 bulan. DM kami untuk portfolio!",
                "permalink": "https://www.threads.net/@recruiter_id/post/C7xYz123",
                "timestamp": "2026-10-26T10:00:00+0000",
                "username": "recruiter_id",
            },
            {
                "id": "18098765432109876",
                "text": "We're hiring a Senior Android Kotlin developer (Jetpack Compose). Send CV to jobs@company.com",
                "permalink": "https://www.threads.net/@tech_corp/post/C8aBc456",
                "timestamp": "2026-10-26T11:30:00+0000",
                "username": "tech_corp",
            },
        ],
        "paging": {
            "cursors": {
                "before": "QVFIUk5...",
                "after": "QVFIUk5v...",
            }
        },
    }


def test_mask_secret():
    assert mask_secret("") == "(empty)"
    assert mask_secret("short") == "********"
    assert mask_secret("TH_ACCESS_TOKEN_SECRET_123456") == "TH_A...3456"


@patch("requests.get")
def test_threads_fetch_success(mock_get, sample_threads_json):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = sample_threads_json
    mock_get.return_value = mock_resp

    source = ThreadsSource(
        access_token="mock_valid_token_123456",
        keywords=["flutter developer"],
        delay_seconds=0,
        max_requests_per_run=1,
    )

    items = source.fetch()
    assert len(items) == 2
    assert items[0].id == "threads_18012345678901234"
    assert "Flutter developer" in items[0].title
    assert items[0].username == "recruiter_id"
    assert items[0].url == "https://www.threads.net/@recruiter_id/post/C7xYz123"
    assert items[1].username == "tech_corp"


@patch("requests.get")
def test_threads_filters_own_username(mock_get, sample_threads_json):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = sample_threads_json
    mock_get.return_value = mock_resp

    source = ThreadsSource(
        access_token="mock_valid_token_123456",
        keywords=["flutter developer"],
        own_username="recruiter_id",  # own username should be skipped
        delay_seconds=0,
        max_requests_per_run=1,
    )

    items = source.fetch()
    assert len(items) == 1
    assert items[0].username == "tech_corp"


@patch("requests.get")
def test_threads_handles_401_token_expired(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 401
    mock_resp.json.return_value = {"error": {"message": "Error validating access token: Session has expired."}}
    mock_get.return_value = mock_resp

    source = ThreadsSource(
        access_token="mock_expired_token",
        keywords=["flutter developer"],
        delay_seconds=0,
    )

    items = source.fetch()
    assert len(items) == 0
    assert source.token_expired_error is True


@patch("requests.get")
def test_threads_handles_403_permission_denied(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 403
    mock_resp.json.return_value = {"error": {"message": "(#10) Application does not have capability."}}
    mock_get.return_value = mock_resp

    source = ThreadsSource(
        access_token="mock_unpermitted_token",
        keywords=["flutter developer"],
        delay_seconds=0,
    )

    items = source.fetch()
    assert len(items) == 0
    assert source.permission_error is True


@patch("requests.get")
def test_threads_token_manager_refresh(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "access_token": "mock_new_long_lived_token_789",
        "token_type": "bearer",
        "expires_in": 5184000,
    }
    mock_get.return_value = mock_resp

    mgr = ThreadsTokenManager(access_token="mock_old_token")
    success, new_tok, expires_in, expiry_str = mgr.refresh_long_lived_token()

    assert success is True
    assert new_tok == "mock_new_long_lived_token_789"
    assert expires_in == 5184000
    assert "UTC" in expiry_str
