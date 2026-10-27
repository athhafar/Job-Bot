"""Unit tests for strict whole-word regex filtering and opportunity qualification."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import pytest

from core.filters import JobFilter, build_keyword_regex
from core.storage import Storage
from sources.base import JobItem


@pytest.fixture
def sample_config():
    return {
        "settings": {
            "max_post_age_hours": 24,
            "max_seen_items": 5000,
        },
        "keywords": {
            "include": [
                "flutter",
                "kotlin",
                "android developer",
                "react native",
                "mobile developer",
                "dart",
                "expo",
            ],
            "hiring": [
                "hiring",
                "dicari",
                "lowongan",
                "butuh",
                "need",
                "looking for",
                "freelance",
                "kontrak",
                "open position",
                "kirim cv",
                "dm",
            ],
            "exclude": [
                "open to work",
                "available for hire",
                "cari kerja",
                "looking for a job",
                "for hire",
                "[for hire]",
                "unpaid",
                "magang",
                "internship",
            ],
        },
    }


@pytest.fixture
def in_memory_storage(tmp_path):
    storage_file = tmp_path / "test_seen.json"
    return Storage(filepath=str(storage_file))


def test_whole_word_regex_prevents_partial_match():
    """Verifies that 'expo' does NOT match 'exposure' or 'exposition'."""
    pattern = build_keyword_regex("expo")
    assert pattern.search("We are using expo SDK 52") is not None
    assert pattern.search("Expo is our primary framework") is not None
    assert pattern.search("High exposure to sunlight") is None
    assert pattern.search("exposition of art") is None


def test_filter_valid_threads_opportunity_passes(sample_config, in_memory_storage):
    job_filter = JobFilter(config=sample_config, storage=in_memory_storage)
    item = JobItem(
        id="threads_1",
        title="Dicari Mobile Developer Flutter untuk kontrak 3 bulan",
        text="Halo teman-teman Threads, kami sedang butuh programmer Flutter freelance. DM saya untuk detailnya ya!",
        url="https://www.threads.net/@recruiter/post/1",
        source="Threads (@recruiter)",
        published=datetime.now(timezone.utc) - timedelta(hours=2),
        username="recruiter",
    )

    passed, reason = job_filter.evaluate(item)
    assert passed is True
    assert "Passed filters" in reason


def test_filter_rejects_exposure_when_only_expo_is_keyword(sample_config, in_memory_storage):
    """Verifies that a post containing 'exposure' does NOT pass as an Expo mobile dev job."""
    job_filter = JobFilter(config=sample_config, storage=in_memory_storage)
    item = JobItem(
        id="threads_2",
        title="We are hiring a Marketing Lead with exposure to digital media",
        text="Need someone with high brand exposure experience.",
        url="https://www.threads.net/@hr/post/2",
        source="Threads",
        published=datetime.now(timezone.utc) - timedelta(hours=1),
    )

    passed, reason = job_filter.evaluate(item)
    assert passed is False
    assert "Missing required mobile developer keyword" in reason


def test_filter_rejects_remote_or_opportunity_standing_alone(sample_config, in_memory_storage):
    """Verifies that 'remote' and 'opportunity' CANNOT stand alone as passing criteria."""
    job_filter = JobFilter(config=sample_config, storage=in_memory_storage)
    # This post has mobile keyword 'flutter', and has 'remote' and 'opportunity',
    # but DOES NOT have any specific hiring signal (hiring, dicari, butuh, freelance, etc.)
    item = JobItem(
        id="threads_3",
        title="Thoughts on Flutter in this remote opportunity era",
        text="Just sharing some insights about how Flutter provides great remote opportunities for developers.",
        url="https://www.threads.net/@dev/post/3",
        source="Threads",
        published=datetime.now(timezone.utc) - timedelta(hours=1),
    )

    passed, reason = job_filter.evaluate(item)
    assert passed is False
    assert "Missing specific hiring/opportunity signal" in reason


def test_filter_rejects_job_seekers(sample_config, in_memory_storage):
    job_filter = JobFilter(config=sample_config, storage=in_memory_storage)
    item = JobItem(
        id="threads_4",
        title="Flutter developer open to work! Looking for a job",
        text="Available for hire as React Native / Flutter developer. Please DM me!",
        url="https://www.threads.net/@jobseeker/post/4",
        source="Threads",
        published=datetime.now(timezone.utc) - timedelta(hours=1),
    )

    passed, reason = job_filter.evaluate(item)
    assert passed is False
    assert "Matched exclude keyword" in reason


def test_filter_rejects_old_post(sample_config, in_memory_storage):
    job_filter = JobFilter(config=sample_config, storage=in_memory_storage)
    item = JobItem(
        id="threads_5",
        title="Hiring Flutter Developer",
        text="We are hiring Flutter developers for freelance contract.",
        url="https://www.threads.net/@co/post/5",
        source="Threads",
        published=datetime.now(timezone.utc) - timedelta(hours=36),
    )

    passed, reason = job_filter.evaluate(item)
    assert passed is False
    assert "Post is too old" in reason


def test_filter_rejects_seen_item(sample_config, in_memory_storage):
    job_filter = JobFilter(config=sample_config, storage=in_memory_storage)
    item = JobItem(
        id="threads_6",
        title="Lowongan Android Developer Kotlin",
        text="Dicari developer Android Kotlin untuk kontrak remote.",
        url="https://www.threads.net/@hr/post/6",
        source="Threads",
        published=datetime.now(timezone.utc) - timedelta(hours=2),
    )

    # First time passes
    passed1, _ = job_filter.evaluate(item)
    assert passed1 is True

    # Mark as seen
    in_memory_storage.mark_seen(item.id, item.url)

    # Second time rejected
    passed2, reason2 = job_filter.evaluate(item)
    assert passed2 is False
    assert "Already processed (seen)" in reason2
