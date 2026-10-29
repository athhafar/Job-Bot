"""Unit tests for ThreadsScraperSource."""
from __future__ import annotations

import json
import os
import subprocess
import tempfile
from unittest.mock import MagicMock, call, patch
import pytest

from sources.threads_scraper import ThreadsScraperError, ThreadsScraperSource


@pytest.fixture
def sample_scraper_posts():
    return [
        {
            "id": "4005886349181858992_38519997895",
            "username": "recruiter_tech",
            "text": "Dibutuhkan Flutter developer untuk pembuatan aplikasi fintech.\nKirim CV ke hr@company.com",
            "timestamp": "2026-10-26T10:00:00Z",
            "permalink": "https://www.threads.net/@recruiter_tech/post/DeXxGkVkjSw",
            "media": [],
        },
        {
            "id": "4014335701407376438_63135117124",
            "username": "my_own_account",
            "text": "Looking for project collaboration in Flutter.",
            "timestamp": "2026-10-26T11:30:00Z",
            "permalink": "https://www.threads.net/@my_own_account/post/De1yQ0zjiQ2",
            "media": [],
        },
    ]


def test_parse_posts_json(sample_scraper_posts):
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(sample_scraper_posts, f)
        temp_path = f.name

    try:
        source = ThreadsScraperSource(
            keywords=["flutter"],
            own_username="my_own_account",
        )
        items = source._parse_posts_json(temp_path)

        # my_own_account should be filtered out
        assert len(items) == 1
        item = items[0]
        assert item.id == "threads_4005886349181858992_38519997895"
        assert item.username == "recruiter_tech"
        assert item.url == "https://www.threads.net/@recruiter_tech/post/DeXxGkVkjSw"
        assert item.source == "threads"
        assert "Dibutuhkan Flutter developer" in item.title
        assert "hr@company.com" in item.text
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


@patch("subprocess.run")
def test_fetch_keyword_success(mock_run, sample_scraper_posts):
    def fake_subprocess_run(cmd, cwd, stdout, stderr, text, timeout):
        # Create fake output structure in cwd
        out_dir = os.path.join(cwd, "output", "search", "keyword", "recent", "flutter")
        os.makedirs(out_dir, exist_ok=True)
        posts_file = os.path.join(out_dir, "posts.json")
        with open(posts_file, "w", encoding="utf-8") as f:
            json.dump(sample_scraper_posts, f)

        res = MagicMock()
        res.returncode = 0
        res.stdout = "Found 2 posts"
        res.stderr = ""
        return res

    mock_run.side_effect = fake_subprocess_run

    source = ThreadsScraperSource(
        keywords=["flutter"],
        delay_range=(0, 0),
    )
    items = source.fetch()
    assert len(items) == 2
    assert items[0].id == "threads_4005886349181858992_38519997895"
    assert items[1].id == "threads_4014335701407376438_63135117124"


@patch("subprocess.run")
def test_fetch_keyword_cli_error(mock_run):
    res = MagicMock()
    res.returncode = 1
    res.stdout = ""
    res.stderr = "Rate limit or network error"
    mock_run.return_value = res

    source = ThreadsScraperSource(
        keywords=["flutter"],
        delay_range=(0, 0),
    )
    items = source.fetch()
    assert len(items) == 0
    assert source.consecutive_errors == 1


@patch("time.sleep")
@patch.object(ThreadsScraperSource, "_fetch_keyword")
def test_delays_between_keywords(mock_fetch, mock_sleep):
    mock_fetch.return_value = []
    source = ThreadsScraperSource(
        keywords=["kw1", "kw2", "kw3"],
        delay_range=(5.0, 5.0),
    )
    source.fetch()

    # Sleep should be called exactly len(keywords) - 1 = 2 times
    assert mock_sleep.call_count == 2
    mock_sleep.assert_has_calls([call(5.0), call(5.0)])


@patch.object(ThreadsScraperSource, "_fetch_keyword")
def test_deduplication_across_keywords(mock_fetch, sample_scraper_posts):
    # Both keywords return the same post
    source = ThreadsScraperSource(
        keywords=["kw1", "kw2"],
        delay_range=(0, 0),
    )
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(sample_scraper_posts, f)
        temp_path = f.name

    try:
        items = source._parse_posts_json(temp_path)
        mock_fetch.return_value = items

        result = source.fetch()
        # Even though fetch was called twice, duplicates must be deduplicated
        assert len(result) == 2
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

