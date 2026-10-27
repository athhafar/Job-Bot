"""Unit tests for multi-stage job pre-filtering logic."""
from datetime import datetime, timezone, timedelta
import pytest

from sources.base import JobItem
from core.storage import Storage
from core.filters import JobFilter


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
                "android",
                "react native",
                "mobile developer",
            ],
            "hiring": [
                "hiring",
                "looking for",
                "freelance",
                "contract",
                "remote",
                "lowongan",
            ],
            "exclude": [
                "unpaid",
                "internship",
                "magang",
                "[for hire]",
                "for hire",
                "looking for a job",
            ],
        },
    }


@pytest.fixture
def in_memory_storage(tmp_path):
    storage_file = tmp_path / "test_seen.json"
    return Storage(filepath=str(storage_file))


def test_filter_valid_opportunity_passes(sample_config, in_memory_storage):
    job_filter = JobFilter(config=sample_config, storage=in_memory_storage)
    item = JobItem(
        id="job_1",
        title="We are hiring a Senior Flutter Developer (Remote)",
        text="Looking for an experienced Flutter engineer to lead our cross-platform app development.",
        url="https://example.com/job1",
        source="Test RSS",
        published=datetime.now(timezone.utc) - timedelta(hours=2),
    )

    passed, reason = job_filter.evaluate(item)
    assert passed is True
    assert "Passed filters" in reason


def test_filter_rejects_missing_mobile_keyword(sample_config, in_memory_storage):
    job_filter = JobFilter(config=sample_config, storage=in_memory_storage)
    item = JobItem(
        id="job_2",
        title="We are hiring a Senior Python Django Backend Developer",
        text="Remote position open for backend API services.",
        url="https://example.com/job2",
        source="Test RSS",
        published=datetime.now(timezone.utc) - timedelta(hours=1),
    )

    passed, reason = job_filter.evaluate(item)
    assert passed is False
    assert "Missing mobile developer include keyword" in reason


def test_filter_rejects_job_seeker_for_hire(sample_config, in_memory_storage):
    job_filter = JobFilter(config=sample_config, storage=in_memory_storage)
    item = JobItem(
        id="job_3",
        title="[FOR HIRE] Experienced Flutter and React Native Developer available for freelance",
        text="I can build your mobile apps with high quality.",
        url="https://example.com/job3",
        source="Reddit: r/forhire",
        published=datetime.now(timezone.utc) - timedelta(hours=1),
    )

    passed, reason = job_filter.evaluate(item)
    assert passed is False
    assert "Matched exclude keyword: '[for hire]'" in reason


def test_filter_rejects_unpaid_or_internship(sample_config, in_memory_storage):
    job_filter = JobFilter(config=sample_config, storage=in_memory_storage)
    item = JobItem(
        id="job_4",
        title="Looking for Android Kotlin Mobile Developer Internship",
        text="Unpaid internship opportunity for students.",
        url="https://example.com/job4",
        source="Test",
        published=datetime.now(timezone.utc) - timedelta(hours=3),
    )

    passed, reason = job_filter.evaluate(item)
    assert passed is False
    assert "Matched exclude keyword" in reason


def test_filter_rejects_old_post(sample_config, in_memory_storage):
    job_filter = JobFilter(config=sample_config, storage=in_memory_storage)
    item = JobItem(
        id="job_5",
        title="Hiring Mobile Developer - Flutter / Kotlin",
        text="Remote role for mobile developer.",
        url="https://example.com/job5",
        source="Test",
        published=datetime.now(timezone.utc) - timedelta(hours=48),
    )

    passed, reason = job_filter.evaluate(item)
    assert passed is False
    assert "Post is too old" in reason


def test_filter_rejects_already_seen_id(sample_config, in_memory_storage):
    job_filter = JobFilter(config=sample_config, storage=in_memory_storage)
    item = JobItem(
        id="job_6",
        title="Hiring React Native Developer (Contract)",
        text="Need developer for mobile application.",
        url="https://example.com/job6",
        source="Test",
        published=datetime.now(timezone.utc) - timedelta(hours=2),
    )

    # First time -> passes
    passed, _ = job_filter.evaluate(item)
    assert passed is True

    # Mark as seen
    in_memory_storage.mark_seen(item.id, item.url)

    # Second time -> rejected as duplicate
    passed2, reason2 = job_filter.evaluate(item)
    assert passed2 is False
    assert "Already processed (seen)" in reason2
