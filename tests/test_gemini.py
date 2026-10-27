"""Unit tests for Gemini AI parsing, error handling, and profile validation."""
from __future__ import annotations

from unittest.mock import MagicMock, patch
import pytest

from core.gemini_client import GeminiClient, validate_profile_content
from sources.base import JobItem
from datetime import datetime, timezone


def test_validate_profile_content_raises_on_placeholder():
    unfilled_profile = """
    # Profil Saya
    - Nama: [Nama Lengkap Anda]
    - GitHub: https://github.com/yourusername
    """
    with pytest.raises(ValueError) as excinfo:
        validate_profile_content(unfilled_profile)
    assert "Isi config/profile.md dulu" in str(excinfo.value)


def test_validate_profile_content_passes_when_filled():
    filled_profile = """
    # Profil Saya
    - Nama: Budi Santoso
    - GitHub: https://github.com/budisantoso
    - Email: budi@gmail.com
    - Keahlian: Flutter & Kotlin
    """
    # Should not raise any error
    validate_profile_content(filled_profile)


def test_parse_json_safely():
    client = GeminiClient(api_key="mock_key")
    raw = """```json
    {
        "is_opportunity": true,
        "relevance": 9,
        "summary": "Peluang kerja Flutter",
        "comment_draft": "Hi! Can help with Flutter.",
        "dm_draft": "Hello, here is my portfolio."
    }
    ```"""
    parsed = client._parse_json_safely(raw)
    assert parsed is not None
    assert parsed["is_opportunity"] is True
    assert parsed["relevance"] == 9
    assert parsed["comment_draft"] == "Hi! Can help with Flutter."


def test_no_fake_score_when_ai_fails():
    """Verifies that if AI fails, relevance is strictly None (no fake score like 7/10)."""
    client = GeminiClient(api_key="mock_key")
    item = JobItem(
        id="threads_123",
        title="Need Flutter Developer",
        text="Need developer for mobile app",
        url="https://www.threads.net/post/123",
        source="Threads",
        published=datetime.now(timezone.utc),
    )
    fallback = client._create_failed_ai_response(item)
    assert fallback["failed_ai"] is True
    assert fallback["relevance"] is None  # CRITICAL: No fake score!
    assert "lolos filter ketat" in fallback["summary"]


@patch("requests.post")
def test_consecutive_429_triggers_quota_exhausted(mock_post):
    mock_resp = MagicMock()
    mock_resp.status_code = 429
    mock_resp.headers = {"Retry-After": "1"}
    mock_post.return_value = mock_resp

    client = GeminiClient(
        api_key="mock_key",
        read_timeout=5,
        inter_call_delay=0,
    )
    # Ensure profile passes
    client.profile_content = "Budi Santoso - Flutter Developer - https://github.com/budi"

    item = JobItem(
        id="threads_999",
        title="Need Kotlin Android Dev",
        text="Need developer for Kotlin app",
        url="https://www.threads.net/post/999",
        source="Threads",
        published=datetime.now(timezone.utc),
    )

    # First call will get 429 (and retry)
    res = client.evaluate_and_draft(item)
    assert res is not None
    assert res["failed_ai"] is True
    assert client.consecutive_429_count >= 2
    assert client.quota_exhausted is True
