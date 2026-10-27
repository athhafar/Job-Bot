"""Unit tests for Gemini response parsing and fallback handling."""
from datetime import datetime, timezone
import pytest

from sources.base import JobItem
from core.gemini_client import GeminiClient


@pytest.fixture
def gemini_client():
    return GeminiClient(
        api_key="",  # empty API key to test offline / fallback logic
        fallback_templates={
            "comment_draft": "Static fallback comment draft",
            "dm_draft": "Static fallback DM draft",
        },
    )


def test_parse_json_safely_clean(gemini_client):
    raw = '{"is_opportunity": true, "relevance": 9, "summary": "Great role", "comment_draft": "Hi", "dm_draft": "Hello"}'
    parsed = gemini_client._parse_json_safely(raw)

    assert parsed is not None
    assert parsed["is_opportunity"] is True
    assert parsed["relevance"] == 9
    assert parsed["summary"] == "Great role"
    assert parsed["comment_draft"] == "Hi"
    assert parsed["dm_draft"] == "Hello"


def test_parse_json_safely_with_markdown_fences(gemini_client):
    raw = """```json
{
  "is_opportunity": true,
  "relevance": 8,
  "summary": "Looking for Flutter dev",
  "comment_draft": "I can help with Flutter!",
  "dm_draft": "DM details"
}
```"""
    parsed = gemini_client._parse_json_safely(raw)

    assert parsed is not None
    assert parsed["is_opportunity"] is True
    assert parsed["relevance"] == 8
    assert "Flutter" in parsed["summary"]


def test_parse_json_safely_with_surrounding_text(gemini_client):
    raw = """Here is my evaluation:
{
  "is_opportunity": false,
  "relevance": 2,
  "summary": "General discussion, not a job",
  "comment_draft": "",
  "dm_draft": ""
}
Hope this helps!"""
    parsed = gemini_client._parse_json_safely(raw)

    assert parsed is not None
    assert parsed["is_opportunity"] is False
    assert parsed["relevance"] == 2


def test_static_fallback_when_api_fails(gemini_client):
    item = JobItem(
        id="sample_job_99",
        title="Urgent: Mobile Flutter App Developer Needed",
        text="Need someone to finish payment integration in 2 weeks.",
        url="https://example.com/job99",
        source="Reddit: r/FlutterDev",
        published=datetime.now(timezone.utc),
    )

    result = gemini_client.evaluate_and_draft(item)

    assert result is not None
    assert result["used_fallback"] is True
    assert result["is_opportunity"] is True
    assert result["comment_draft"] == "Static fallback comment draft"
    assert result["dm_draft"] == "Static fallback DM draft"
